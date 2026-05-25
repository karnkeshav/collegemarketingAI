"""
Scraping endpoints with Server-Sent Events (SSE) progress streaming.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, AsyncSessionLocal
from models import College, Contact, State
from scrapers.aicte_scraper import fetch_aicte_colleges
from scrapers.college_scraper import scrape_college_emails
from services.email_validator import validate_email_address
from schemas import ScrapeRequest

router = APIRouter(prefix="/api/scrape", tags=["scraper"])
logger = logging.getLogger(__name__)

# Global scrape progress store (in-memory per state)
scrape_progress: dict[str, dict] = {}


@router.post("/start")
async def start_scrape(
    req: ScrapeRequest,
    background_tasks: BackgroundTasks,
):
    if req.state_code:
        key = req.state_code.upper()
        if scrape_progress.get(key, {}).get("status") == "running":
            return {"message": f"Scrape already running for {key}"}
        scrape_progress[key] = {"status": "running", "done": 0, "total": 0, "log": []}
        background_tasks.add_task(_scrape_state, key)
        return {"message": f"Scrape started for {key}"}
    elif req.college_id:
        background_tasks.add_task(_scrape_single_college, req.college_id)
        return {"message": f"Scrape started for college {req.college_id}"}
    return {"message": "No target specified"}


@router.get("/status")
async def scrape_status():
    return scrape_progress


@router.get("/stream/{state_code}")
async def scrape_stream(state_code: str):
    """SSE endpoint for real-time progress updates."""
    async def event_gen() -> AsyncGenerator[str, None]:
        state_code_upper = state_code.upper()
        last_done = -1
        timeout = 0
        while True:
            progress = scrape_progress.get(state_code_upper, {})
            done = progress.get("done", 0)
            status = progress.get("status", "idle")

            if done != last_done:
                last_done = done
                yield f"data: {json.dumps(progress)}\n\n"
                timeout = 0

            if status in ("done", "failed"):
                yield f"data: {json.dumps(progress)}\n\n"
                break

            await asyncio.sleep(1)
            timeout += 1
            if timeout > 600:
                break

    return StreamingResponse(event_gen(), media_type="text/event-stream")


async def _scrape_state(state_code: str) -> None:
    try:
        async with AsyncSessionLocal() as db:
            state_result = await db.execute(select(State).where(State.code == state_code))
            state = state_result.scalar_one_or_none()
            if not state:
                scrape_progress[state_code] = {"status": "failed", "log": ["State not found"]}
                return

        _log(state_code, f"Fetching AICTE colleges for {state_code}...")
        aicte_colleges = await fetch_aicte_colleges(state_code)
        _log(state_code, f"Found {len(aicte_colleges)} colleges from AICTE")

        scrape_progress[state_code]["total"] = len(aicte_colleges)

        saved_colleges = []
        async with AsyncSessionLocal() as db:
            for college_data in aicte_colleges:
                college = await _upsert_college(db, college_data, state.id)
                saved_colleges.append(college)
            await db.commit()

        # Re-fetch committed college IDs
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(College).where(College.state_id == state.id)
            )
            saved_colleges = result.scalars().all()

        scrape_progress[state_code]["total"] = len(saved_colleges)

        for i, college in enumerate(saved_colleges):
            _log(state_code, f"[{i+1}/{len(saved_colleges)}] Scraping: {college.name}")
            await _scrape_college_contacts(college.id)
            scrape_progress[state_code]["done"] = i + 1
            await asyncio.sleep(1)

        scrape_progress[state_code]["status"] = "done"
        _log(state_code, "Scrape complete.")

    except Exception as e:
        logger.error(f"Scrape error for {state_code}: {e}")
        scrape_progress[state_code]["status"] = "failed"
        _log(state_code, f"Error: {e}")


async def _scrape_single_college(college_id: int) -> None:
    await _scrape_college_contacts(college_id)


async def _upsert_college(db: AsyncSession, data: dict, state_id: int) -> College:
    """Insert or update a college record."""
    existing = None
    if data.get("aicte_code"):
        result = await db.execute(
            select(College).where(College.aicte_code == data["aicte_code"])
        )
        existing = result.scalar_one_or_none()

    if not existing and data.get("name"):
        result = await db.execute(
            select(College).where(
                College.name == data["name"],
                College.state_id == state_id,
            )
        )
        existing = result.scalar_one_or_none()

    if existing:
        existing.website = data.get("website") or existing.website
        existing.city = data.get("city") or existing.city
        existing.college_type = data.get("college_type") or existing.college_type
        db.add(existing)
        college = existing
    else:
        college = College(
            name=data["name"],
            state_id=state_id,
            city=data.get("city", ""),
            website=data.get("website", ""),
            college_type=data.get("college_type", "Engineering"),
            aicte_code=data.get("aicte_code", ""),
            address=data.get("address", ""),
            scrape_status="pending",
        )
        db.add(college)
        await db.flush()

    # Save direct AICTE email immediately if present
    if data.get("email"):
        await _upsert_contact(
            db,
            college_id=college.id,
            email=data["email"],
            name=data.get("contact_name", ""),
            role="Principal",
            source_url="https://facilities.aicte-india.org",
        )

    return college


async def _scrape_college_contacts(college_id: int) -> None:
    async with AsyncSessionLocal() as db:
        college = await db.get(College, college_id)
        if not college:
            return

        college.scrape_status = "scraping"
        db.add(college)
        await db.commit()

        try:
            contacts = await scrape_college_emails(college.website, college.name)

            for contact_data in contacts:
                email = contact_data.get("email", "").lower().strip()
                if not email:
                    continue
                is_valid, _ = await validate_email_address(email)
                if not is_valid:
                    continue
                await _upsert_contact(
                    db,
                    college_id=college.id,
                    email=email,
                    name=contact_data.get("name", ""),
                    role=contact_data.get("role", "General"),
                    source_url=contact_data.get("source_url", ""),
                )

            college.scrape_status = "done"
            college.last_scraped = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error scraping college {college_id}: {e}")
            college.scrape_status = "failed"

        db.add(college)
        await db.commit()


async def _upsert_contact(
    db: AsyncSession,
    college_id: int,
    email: str,
    name: str,
    role: str,
    source_url: str,
) -> None:
    result = await db.execute(select(Contact).where(Contact.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        return

    contact = Contact(
        college_id=college_id,
        email=email,
        name=name,
        role=role,
        source_url=source_url,
        validation_status="unvalidated",
    )
    db.add(contact)


def _log(state_code: str, message: str) -> None:
    logger.info(message)
    progress = scrape_progress.setdefault(state_code, {})
    logs = progress.setdefault("log", [])
    logs.append(message)
    if len(logs) > 50:
        logs.pop(0)
