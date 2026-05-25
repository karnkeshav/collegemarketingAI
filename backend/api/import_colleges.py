"""
CSV import for colleges.
Expected CSV columns (flexible — uses header matching):
  name, city, state_code, website, college_type, aicte_code (all optional except name+state)
"""
import csv
import io
import logging

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import College, State

router = APIRouter(prefix="/api/colleges", tags=["colleges"])
logger = logging.getLogger(__name__)

HEADER_ALIASES = {
    "name": ["name", "college name", "institution name", "institute name", "college"],
    "city": ["city", "district", "location", "town"],
    "state_code": ["state_code", "state code", "state", "statecode"],
    "website": ["website", "url", "web", "site", "website url"],
    "college_type": ["college_type", "type", "category", "college type", "course type"],
    "aicte_code": ["aicte_code", "aicte code", "code", "inst_code"],
}


def _map_headers(header_row: list[str]) -> dict[str, int]:
    """Map CSV column headers to our field names, case-insensitively."""
    header_lower = [h.strip().lower() for h in header_row]
    mapping = {}
    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias in header_lower:
                mapping[field] = header_lower.index(alias)
                break
    return mapping


@router.post("/import")
async def import_colleges_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")  # handle BOM
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise HTTPException(400, "CSV is empty")

    col_map = _map_headers(rows[0])
    if "name" not in col_map:
        raise HTTPException(400, "CSV must have a 'name' column")

    # Load state lookup
    state_result = await db.execute(select(State))
    states = state_result.scalars().all()
    state_by_code = {s.code.upper(): s for s in states}
    state_by_name = {s.name.lower(): s for s in states}

    added = 0
    skipped = 0
    errors = []

    for i, row in enumerate(rows[1:], start=2):
        if not row or not any(row):
            continue
        try:
            name = row[col_map["name"]].strip() if "name" in col_map else ""
            if not name:
                continue

            # Resolve state
            state = None
            if "state_code" in col_map and col_map["state_code"] < len(row):
                raw = row[col_map["state_code"]].strip().upper()
                state = state_by_code.get(raw) or state_by_name.get(raw.lower())
            if not state:
                # Default to Telangana if unknown
                state = state_by_code.get("TS")

            city = row[col_map["city"]].strip() if "city" in col_map and col_map["city"] < len(row) else ""
            website = row[col_map["website"]].strip() if "website" in col_map and col_map["website"] < len(row) else ""
            college_type = row[col_map["college_type"]].strip() if "college_type" in col_map and col_map["college_type"] < len(row) else ""
            aicte_code = row[col_map["aicte_code"]].strip() if "aicte_code" in col_map and col_map["aicte_code"] < len(row) else ""

            if website and not website.startswith("http"):
                website = "https://" + website

            # Check duplicate by name+state
            dup = await db.execute(
                select(College).where(College.name == name, College.state_id == state.id)
            )
            if dup.scalar_one_or_none():
                skipped += 1
                continue

            college = College(
                name=name,
                state_id=state.id,
                city=city,
                website=website,
                college_type=college_type or "General",
                aicte_code=aicte_code,
                scrape_status="pending",
            )
            db.add(college)
            added += 1

        except Exception as e:
            errors.append(f"Row {i}: {e}")

    await db.commit()

    return {
        "added": added,
        "skipped_duplicates": skipped,
        "errors": errors[:10],
        "message": f"Imported {added} colleges ({skipped} duplicates skipped)",
    }


@router.get("/template")
async def download_import_template():
    """Return a sample CSV template for college import."""
    from fastapi.responses import StreamingResponse
    sample = (
        "name,city,state_code,website,college_type,aicte_code\n"
        "JNTU Hyderabad,Hyderabad,TS,https://jntuh.ac.in,Engineering,\n"
        "Osmania University,Hyderabad,TS,https://osmania.ac.in,Arts,\n"
        "NIT Patna,Patna,BR,https://nitp.ac.in,Engineering,\n"
        "IIT Dhanbad,Dhanbad,JH,https://iitism.ac.in,Engineering,\n"
        "Delhi University,Delhi,DL,https://du.ac.in,Arts,\n"
        "Andhra University,Visakhapatnam,AP,https://andhrauniversity.edu.in,General,\n"
    )
    return StreamingResponse(
        io.BytesIO(sample.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=college_import_template.csv"},
    )
