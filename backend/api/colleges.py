from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from database import get_db
from models import College, State, Contact
from schemas import CollegeOut

router = APIRouter(prefix="/api/colleges", tags=["colleges"])


@router.get("", response_model=dict)
async def list_colleges(
    state_code: Optional[str] = Query(None),
    college_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(College)

    if state_code:
        state_sub = select(State.id).where(State.code == state_code.upper())
        query = query.where(College.state_id.in_(state_sub))
    if college_type:
        query = query.where(College.college_type.ilike(f"%{college_type}%"))
    if search:
        query = query.where(College.name.ilike(f"%{search}%"))

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.order_by(College.name).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    colleges = result.scalars().all()

    out = []
    for c in colleges:
        state_result = await db.get(State, c.state_id)
        contact_count_result = await db.execute(
            select(func.count(Contact.id)).where(Contact.college_id == c.id)
        )
        contact_count = contact_count_result.scalar()
        out.append({
            "id": c.id,
            "name": c.name,
            "state_id": c.state_id,
            "state_name": state_result.name if state_result else "",
            "city": c.city,
            "college_type": c.college_type,
            "streams": c.streams,
            "website": c.website,
            "address": c.address,
            "aicte_code": c.aicte_code,
            "naac_grade": c.naac_grade,
            "scrape_status": c.scrape_status,
            "last_scraped": c.last_scraped,
            "contact_count": contact_count,
            "created_at": c.created_at,
        })

    return {"items": out, "total": total, "page": page, "limit": limit}
