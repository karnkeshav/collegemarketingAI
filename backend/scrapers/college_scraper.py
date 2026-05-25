"""
Visits individual college websites and extracts contact emails
with role inference from surrounding text context.
"""
import asyncio
import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contact_us",
    "/contactus",
    "/about",
    "/about-us",
    "/administration",
    "/placement",
    "/placement-cell",
    "/training-placement",
    "/training_placement",
    "/faculty",
    "/staff",
    "/team",
    "/our-team",
]

ROLE_KEYWORDS = {
    "TPO": [
        "placement officer", "training placement", "tpo", "placement coordinator",
        "placement cell", "t&p", "training and placement", "campus placement",
    ],
    "Principal": [
        "principal", "director", "vice chancellor", "chancellor", "rector",
    ],
    "Chairman": [
        "chairman", "chairperson", "managing director", "president", "founder",
        "managing trustee", "secretary",
    ],
    "HOD": [
        "head of department", "hod", "department head", "head of the department",
    ],
    "Dean": [
        "dean", "academic dean", "dean of students", "dean research",
    ],
}

SKIP_EMAILS = {
    "example.com", "test.com", "domain.com", "email.com",
    "yourmail.com", "abc.com", "xyz.com", "sample.com",
}


async def scrape_college_emails(website: str, college_name: str = "") -> list[dict]:
    """
    Visits a college website and returns a list of contact dicts:
    {email, name, role, source_url, confidence}
    """
    if not website:
        return []

    base = _normalise_base(website)
    if not base:
        return []

    found: dict[str, dict] = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CollegeContactBot/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }

    async with httpx.AsyncClient(
        timeout=15, headers=headers, follow_redirects=True, verify=False
    ) as client:
        urls_to_try = [base] + [urljoin(base, p) for p in CONTACT_PATHS]

        for url in urls_to_try:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                ct = resp.headers.get("content-type", "")
                if "html" not in ct:
                    continue

                emails = _extract_emails_with_context(resp.text, url)
                for item in emails:
                    email = item["email"]
                    domain = email.split("@")[-1].lower()
                    if domain in SKIP_EMAILS:
                        continue
                    if email not in found or item["confidence"] > found[email]["confidence"]:
                        found[email] = item
            except Exception:
                continue
            await asyncio.sleep(0.3)

    return list(found.values())


def _normalise_base(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _extract_emails_with_context(html: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text_lower = text.lower()

    results = []
    for match in EMAIL_RE.finditer(text):
        email = match.group(0).lower()
        start = max(0, match.start() - 300)
        end = min(len(text), match.end() + 300)
        context = text[start:end].lower()

        role, confidence = _infer_role(context)
        results.append(
            {
                "email": email,
                "role": role,
                "confidence": confidence,
                "source_url": source_url,
                "name": _extract_nearby_name(text, match.start()),
            }
        )

    return results


def _infer_role(context: str) -> tuple[str, int]:
    best_role = "General"
    best_score = 0

    for role, keywords in ROLE_KEYWORDS.items():
        score = sum(10 for kw in keywords if kw in context)
        if score > best_score:
            best_score = score
            best_role = role

    return best_role, best_score


def _extract_nearby_name(text: str, email_pos: int) -> str:
    start = max(0, email_pos - 150)
    end = min(len(text), email_pos + 50)
    snippet = text[start:end]

    name_re = re.compile(r"\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)\b")
    matches = name_re.findall(snippet)
    return matches[-1] if matches else ""
