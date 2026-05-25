import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from database import get_db
from models import Contact, College, State, CampaignSend
from schemas import ValidateRequest
from services.email_validator import batch_validate
from services.csv_service import contacts_to_csv

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=dict)
async def list_contacts(
    state_code: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    validation_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Contact, College.name.label("college_name"), State.name.label("state_name"),
               College.city, College.college_type)
        .join(College, Contact.college_id == College.id)
        .join(State, College.state_id == State.id)
    )

    if state_code:
        query = query.where(State.code == state_code.upper())
    if role:
        query = query.where(Contact.role == role)
    if validation_status:
        query = query.where(Contact.validation_status == validation_status)
    if search:
        query = query.where(
            Contact.email.ilike(f"%{search}%") | Contact.name.ilike(f"%{search}%")
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Contact.created_at.desc()).offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(query)).all()

    out = []
    for row in rows:
        c, college_name, state_name, city, college_type = row
        sends_count = (await db.execute(
            select(func.count(CampaignSend.id)).where(CampaignSend.contact_id == c.id)
        )).scalar()
        out.append({
            "id": c.id,
            "college_id": c.college_id,
            "college_name": college_name,
            "state_name": state_name,
            "city": city,
            "college_type": college_type,
            "name": c.name,
            "role": c.role,
            "email": c.email,
            "department": c.department,
            "phone": c.phone,
            "source_url": c.source_url,
            "validation_status": c.validation_status,
            "mx_valid": c.mx_valid,
            "is_unsubscribed": c.is_unsubscribed,
            "campaigns_sent": sends_count,
            "created_at": c.created_at,
        })

    return {"items": out, "total": total, "page": page, "limit": limit}


@router.post("/validate")
async def validate_contacts(req: ValidateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Contact).where(Contact.id.in_(req.contact_ids))
    )
    contacts = result.scalars().all()
    emails = [c.email for c in contacts]

    validation_results = await batch_validate(emails)

    updated = 0
    for c in contacts:
        valid, reason = validation_results.get(c.email, (False, "not checked"))
        c.validation_status = "valid" if valid else "invalid"
        c.mx_valid = valid
        db.add(c)
        updated += 1

    await db.commit()
    return {"updated": updated, "results": {e: {"valid": v, "reason": r} for e, (v, r) in validation_results.items()}}


@router.get("/export")
async def export_csv(
    state_code: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    validation_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Contact, College.name.label("college_name"), State.name.label("state_name"),
               College.city, College.college_type)
        .join(College, Contact.college_id == College.id)
        .join(State, College.state_id == State.id)
        .where(Contact.is_unsubscribed == False)
    )

    if state_code:
        query = query.where(State.code == state_code.upper())
    if role:
        query = query.where(Contact.role == role)
    if validation_status:
        query = query.where(Contact.validation_status == validation_status)

    rows = (await db.execute(query)).all()

    contacts_data = []
    for row in rows:
        c, college_name, state_name, city, college_type = row
        contacts_data.append({
            "id": c.id,
            "college_name": college_name,
            "state_name": state_name,
            "city": city,
            "college_type": college_type,
            "name": c.name,
            "role": c.role,
            "email": c.email,
            "department": c.department,
            "phone": c.phone,
            "validation_status": c.validation_status,
            "source_url": c.source_url,
            "created_at": str(c.created_at),
        })

    csv_content = contacts_to_csv(contacts_data)
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


@router.patch("/{contact_id}/unsubscribe")
async def unsubscribe_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact:
        from fastapi import HTTPException
        raise HTTPException(404, "Contact not found")
    contact.is_unsubscribed = True
    db.add(contact)
    await db.commit()
    return {"success": True}
