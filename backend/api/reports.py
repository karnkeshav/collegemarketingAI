from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models import College, Contact, Campaign, CampaignSend, State

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    total_colleges = (await db.execute(select(func.count(College.id)))).scalar()
    total_contacts = (await db.execute(select(func.count(Contact.id)))).scalar()
    validated_contacts = (await db.execute(
        select(func.count(Contact.id)).where(Contact.validation_status == "valid")
    )).scalar()
    invalid_contacts = (await db.execute(
        select(func.count(Contact.id)).where(Contact.validation_status == "invalid")
    )).scalar()
    total_campaigns = (await db.execute(select(func.count(Campaign.id)))).scalar()
    emails_sent = (await db.execute(
        select(func.count(CampaignSend.id)).where(CampaignSend.status == "sent")
    )).scalar()
    emails_bounced = (await db.execute(
        select(func.count(CampaignSend.id)).where(CampaignSend.status == "bounced")
    )).scalar()

    # Per-state breakdown
    states_result = await db.execute(
        select(
            State.name,
            State.code,
            func.count(College.id).label("college_count"),
        )
        .join(College, College.state_id == State.id, isouter=True)
        .group_by(State.id)
    )
    by_state = [
        {"state": row.name, "code": row.code, "colleges": row.college_count}
        for row in states_result
    ]

    # Contact count per state
    contacts_state_result = await db.execute(
        select(State.name, func.count(Contact.id).label("contact_count"))
        .join(College, College.state_id == State.id)
        .join(Contact, Contact.college_id == College.id, isouter=True)
        .group_by(State.id)
    )
    contact_by_state = {row.name: row.contact_count for row in contacts_state_result}
    for s in by_state:
        s["contacts"] = contact_by_state.get(s["state"], 0)

    # Per-role breakdown
    roles_result = await db.execute(
        select(Contact.role, func.count(Contact.id).label("count"))
        .group_by(Contact.role)
    )
    by_role = [{"role": row.role, "count": row.count} for row in roles_result]

    return {
        "total_colleges": total_colleges,
        "total_contacts": total_contacts,
        "validated_contacts": validated_contacts,
        "invalid_contacts": invalid_contacts,
        "total_campaigns": total_campaigns,
        "emails_sent": emails_sent,
        "emails_bounced": emails_bounced,
        "by_state": by_state,
        "by_role": by_role,
    }


@router.get("/campaigns/{campaign_id}/sends")
async def campaign_sends(campaign_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(
            CampaignSend,
            Contact.email,
            Contact.name,
            Contact.role,
            College.name.label("college_name"),
        )
        .join(Contact, CampaignSend.contact_id == Contact.id)
        .join(College, Contact.college_id == College.id)
        .where(CampaignSend.campaign_id == campaign_id)
        .order_by(CampaignSend.status, CampaignSend.sent_at.desc())
    )).all()

    return {
        "items": [
            {
                "id": s.id,
                "contact_email": email,
                "contact_name": name,
                "role": role,
                "college_name": college_name,
                "status": s.status,
                "sent_at": s.sent_at,
                "error_message": s.error_message,
                "bounce_detected_at": s.bounce_detected_at,
            }
            for s, email, name, role, college_name in rows
        ]
    }
