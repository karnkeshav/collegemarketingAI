"""
Scrapes AICTE approved institution data.
AICTE's public portal: https://facilities.aicte-india.org
"""
import asyncio
import json
import logging
import re
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

AICTE_API = "https://facilities.aicte-india.org/dashboard/pages/getinstitutes.php"

STATE_MAP = {
    "TS": "TELANGANA",
    "AP": "ANDHRA PRADESH",
    "BR": "BIHAR",
    "JH": "JHARKHAND",
    "DL": "DELHI",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://facilities.aicte-india.org/",
    "Content-Type": "application/x-www-form-urlencoded",
}


async def fetch_aicte_colleges(state_code: str) -> list[dict]:
    """Fetch all AICTE-approved institutions for a state."""
    state_name = STATE_MAP.get(state_code.upper(), state_code.upper())
    colleges = []

    try:
        async with httpx.AsyncClient(timeout=30, headers=HEADERS, verify=False) as client:
            payload = {
                "state": state_name,
                "course_type": "ALL",
                "intake_year": "2024-25",
            }
            resp = await client.post(AICTE_API, data=payload)
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, list):
                raw_list = data
            elif isinstance(data, dict):
                raw_list = data.get("data", data.get("institutes", []))
            else:
                raw_list = []

            for inst in raw_list:
                college = _parse_aicte_record(inst, state_code)
                if college:
                    colleges.append(college)

    except Exception as e:
        logger.warning(f"AICTE fetch failed for {state_code}: {e}")
        colleges = await _fallback_aicte_fetch(state_code)

    return colleges


async def _fallback_aicte_fetch(state_code: str) -> list[dict]:
    """Try alternate AICTE endpoint format."""
    state_name = STATE_MAP.get(state_code.upper(), state_code.upper())
    colleges = []
    try:
        async with httpx.AsyncClient(timeout=30, headers=HEADERS, verify=False) as client:
            for page in range(1, 20):
                payload = {
                    "draw": str(page),
                    "start": str((page - 1) * 100),
                    "length": "100",
                    "state": state_name,
                }
                resp = await client.post(AICTE_API, data=payload)
                if resp.status_code != 200:
                    break
                try:
                    data = resp.json()
                except Exception:
                    break
                records = data.get("data", [])
                if not records:
                    break
                for inst in records:
                    college = _parse_aicte_record(inst, state_code)
                    if college:
                        colleges.append(college)
                if len(records) < 100:
                    break
                await asyncio.sleep(0.5)
    except Exception as e:
        logger.warning(f"Fallback AICTE fetch failed for {state_code}: {e}")
    return colleges


def _parse_aicte_record(inst: dict | list, state_code: str) -> dict | None:
    """Normalise a raw AICTE institution record into our schema."""
    if isinstance(inst, list):
        if len(inst) < 3:
            return None
        return {
            "name": str(inst[1]).strip() if len(inst) > 1 else "",
            "city": str(inst[3]).strip() if len(inst) > 3 else "",
            "website": _clean_url(str(inst[5]) if len(inst) > 5 else ""),
            "aicte_code": str(inst[0]).strip() if inst else "",
            "college_type": str(inst[4]).strip() if len(inst) > 4 else "Engineering",
            "address": "",
            "email": _extract_email(str(inst[6]) if len(inst) > 6 else ""),
            "contact_name": str(inst[7]).strip() if len(inst) > 7 else "",
            "state_code": state_code,
        }

    name = (
        inst.get("ins_name") or inst.get("name") or inst.get("Institute_Name") or ""
    ).strip()
    if not name:
        return None

    return {
        "name": name,
        "city": (inst.get("city") or inst.get("City") or inst.get("district") or "").strip(),
        "website": _clean_url(
            inst.get("website") or inst.get("Website") or inst.get("ins_url") or ""
        ),
        "aicte_code": (inst.get("inst_code") or inst.get("aicte_code") or "").strip(),
        "college_type": (
            inst.get("course_type") or inst.get("type") or inst.get("Category") or "Engineering"
        ).strip(),
        "address": (inst.get("address") or inst.get("Address") or "").strip(),
        "email": _extract_email(
            inst.get("email") or inst.get("Email") or inst.get("contact_mail") or ""
        ),
        "contact_name": (
            inst.get("contact_name") or inst.get("principal") or inst.get("Director") or ""
        ).strip(),
        "state_code": state_code,
    }


def _clean_url(url: str) -> str:
    url = url.strip()
    if not url or url.lower() in ("n/a", "na", "-", "nil"):
        return ""
    if url and not url.startswith("http"):
        url = "https://" + url
    return url


def _extract_email(text: str) -> str:
    text = text.strip()
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0).lower() if match else ""
