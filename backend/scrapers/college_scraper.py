"""
Visits individual college websites and extracts contact emails
with role inference from surrounding text context.
Handles static HTML, PHP-rendered pages, and meta-refresh redirects.
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
    "",
    "/contact",
    "/contact-us",
    "/contact_us",
    "/contactus",
    "/contact.php",
    "/contact.html",
    "/about",
    "/about-us",
    "/about.php",
    "/administration",
    "/administration.php",
    "/placement",
    "/placement-cell",
    "/placement.php",
    "/training-placement",
    "/training_placement",
    "/tpo",
    "/faculty",
    "/faculty.php",
    "/staff",
    "/staff.php",
    "/team",
    "/our-team",
    "/people",
    "/directory",
    "/reach-us",
    "/reachus",
]

ROLE_KEYWORDS = {
    "TPO": [
        "placement officer", "training placement", "tpo", "placement coordinator",
        "placement cell", "t&p", "training and placement", "campus placement",
        "placement in-charge", "placement incharge",
    ],
    "Principal": [
        "principal", "director", "vice chancellor", "chancellor", "rector",
        "head of institution", "pro vice chancellor",
    ],
    "Chairman": [
        "chairman", "chairperson", "managing director", "president", "founder",
        "managing trustee", "secretary", "correspondent", "ceo",
    ],
    "HOD": [
        "head of department", "hod", "department head", "head of the department",
        "dept. head", "prof. & head",
    ],
    "Dean": [
        "dean", "academic dean", "dean of students", "dean research",
        "dean academics",
    ],
}

SKIP_DOMAINS = {
    "example.com", "test.com", "domain.com", "email.com",
    "yourmail.com", "abc.com", "xyz.com", "sample.com",
    "sentry.io", "google.com", "facebook.com", "twitter.com",
    "w3.org", "schema.org", "openstreetmap.org",
}

SKIP_PREFIXES = {
    "noreply", "no-reply", "donotreply", "webmaster@w3", "support@sentry",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
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

    async with httpx.AsyncClient(
        timeout=20,
        headers=HEADERS,
        follow_redirects=True,
        verify=False,
    ) as client:
        # Try base URL first to detect actual domain (some redirect)
        actual_base = base
        try:
            resp = await client.get(base)
            actual_base = _normalise_base(str(resp.url))
        except Exception:
            pass

        urls_to_try = [actual_base] + [urljoin(actual_base, p) for p in CONTACT_PATHS[1:]]

        for url in urls_to_try:
            if len(found) >= 30:  # enough emails, stop
                break
            try:
                resp = await client.get(url)
                if resp.status_code not in (200, 203):
                    continue
                ct = resp.headers.get("content-type", "")
                if "html" not in ct and "text" not in ct:
                    continue

                emails = _extract_emails_with_context(resp.text, url)
                for item in emails:
                    email = item["email"]
                    domain = email.split("@")[-1].lower()

                    # Skip bad domains
                    if domain in SKIP_DOMAINS:
                        continue
                    # Skip generic noreply
                    local = email.split("@")[0].lower()
                    if any(local.startswith(p) for p in SKIP_PREFIXES):
                        continue
                    # Skip image-looking strings
                    if any(email.lower().endswith(ext) for ext in [".png", ".jpg", ".gif", ".svg"]):
                        continue

                    if email not in found or item["confidence"] > found[email]["confidence"]:
                        found[email] = item

            except Exception:
                continue

            await asyncio.sleep(0.5)

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
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "head"]):
        tag.decompose()

    # Also check for mailto: links — very reliable
    mailto_emails = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            email = href[7:].split("?")[0].strip().lower()
            if EMAIL_RE.match(email):
                context = (a.get_text() + " " + a.parent.get_text() if a.parent else a.get_text()).lower()
                role, confidence = _infer_role(context)
                mailto_emails.append({
                    "email": email,
                    "role": role,
                    "confidence": confidence + 20,  # mailto is more reliable
                    "source_url": source_url,
                    "name": _extract_nearby_name(a.get_text() + " " + (a.parent.get_text() if a.parent else ""), 100),
                })

    text = soup.get_text(separator=" ")
    text_results = []
    for match in EMAIL_RE.finditer(text):
        email = match.group(0).lower()
        start = max(0, match.start() - 300)
        end = min(len(text), match.end() + 300)
        context = text[start:end].lower()
        role, confidence = _infer_role(context)
        text_results.append({
            "email": email,
            "role": role,
            "confidence": confidence,
            "source_url": source_url,
            "name": _extract_nearby_name(text, match.start()),
        })

    # Merge: mailto takes priority
    merged: dict[str, dict] = {}
    for item in text_results + mailto_emails:
        e = item["email"]
        if e not in merged or item["confidence"] > merged[e]["confidence"]:
            merged[e] = item

    return list(merged.values())


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
    start = max(0, email_pos - 200)
    end = min(len(text), email_pos + 60)
    snippet = text[start:end]
    name_re = re.compile(r"\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)\b")
    matches = name_re.findall(snippet)
    # Filter out obvious non-names
    bad = {"Home Page", "Contact Us", "About Us", "Head Office", "Email Id", "Phone Number"}
    names = [m for m in matches if m not in bad]
    return names[-1] if names else ""
