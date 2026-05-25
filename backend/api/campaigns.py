import asyncio
import io
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db, AsyncSessionLocal
from models import Campaign, CampaignSend, Contact, College, State
from schemas import CampaignOut, SendCampaignRequest
from services.email_sender import send_bulk
from services.bounce_checker import check_bounces
from services.csv_service import campaign_report_to_csv

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])
logger = logging.getLogger(__name__)


@router.post("", response_model=dict)
async def create_campaign(
    name: str = Form(...),
    subject: str = Form(...),
    template: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await template.read()
    html = content.decode("utf-8", errors="replace")

    campaign = Campaign(
        name=name,
        subject=subject,
        template_html=html,
        template_filename=template.filename or "template.html",
        status="draft",
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return {"id": campaign.id, "name": campaign.name, "status": campaign.status}


@router.get("", response_model=dict)
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    campaigns = result.scalars().all()
    return {
        "items": [
            {
                "id": c.id,
                "name": c.name,
                "subject": c.subject,
                "template_filename": c.template_filename,
                "status": c.status,
                "created_at": c.created_at,
                "sent_at": c.sent_at,
                "total_recipients": c.total_recipients,
                "sent_count": c.sent_count,
                "bounced_count": c.bounced_count,
                "failed_count": c.failed_count,
            }
            for c in campaigns
        ]
    }


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return {
        "id": campaign.id,
        "name": campaign.name,
        "subject": campaign.subject,
        "template_html": campaign.template_html,
        "template_filename": campaign.template_filename,
        "status": campaign.status,
        "created_at": campaign.created_at,
        "sent_at": campaign.sent_at,
        "total_recipients": campaign.total_recipients,
        "sent_count": campaign.sent_count,
        "bounced_count": campaign.bounced_count,
        "failed_count": campaign.failed_count,
    }


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    req: SendCampaignRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status == "sending":
        raise HTTPException(400, "Campaign is already sending")

    # Resolve recipient list
    query = (
        select(Contact, College.name.label("college_name"))
        .join(College, Contact.college_id == College.id)
        .join(State, College.state_id == State.id)
        .where(Contact.is_unsubscribed == False)
        .where(Contact.validation_status != "invalid")
    )

    if req.contact_ids:
        query = query.where(Contact.id.in_(req.contact_ids))
    else:
        if req.state_codes:
            query = query.where(State.code.in_([s.upper() for s in req.state_codes]))
        if req.roles:
            query = query.where(Contact.role.in_(req.roles))

    rows = (await db.execute(query)).all()
    recipients = [
        {"contact_id": c.id, "email": c.email, "name": c.name, "college": college_name}
        for c, college_name in rows
    ]

    if not recipients:
        raise HTTPException(400, "No eligible recipients found")

    # Create send records
    for r in recipients:
        db.add(CampaignSend(
            campaign_id=campaign_id,
            contact_id=r["contact_id"],
            status="pending",
        ))

    campaign.status = "sending"
    campaign.total_recipients = len(recipients)
    campaign.sent_at = datetime.utcnow()
    db.add(campaign)
    await db.commit()

    background_tasks.add_task(
        _run_campaign_send, campaign_id, recipients, campaign.subject, campaign.template_html
    )

    return {"message": f"Sending to {len(recipients)} recipients", "total": len(recipients)}


@router.get("/{campaign_id}/status")
async def campaign_status(campaign_id: int, db: AsyncSession = Depends(get_db)):
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    sends_result = await db.execute(
        select(
            CampaignSend.status,
            func.count(CampaignSend.id).label("count"),
        )
        .where(CampaignSend.campaign_id == campaign_id)
        .group_by(CampaignSend.status)
    )
    by_status = {row.status: row.count for row in sends_result}

    return {
        "id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "total_recipients": campaign.total_recipients,
        "sent_count": campaign.sent_count,
        "bounced_count": campaign.bounced_count,
        "failed_count": campaign.failed_count,
        "by_status": by_status,
    }


@router.post("/{campaign_id}/check-bounces")
async def check_campaign_bounces(campaign_id: int, db: AsyncSession = Depends(get_db)):
    """Poll Gmail IMAP for NDR emails and mark bounced sends."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    loop = asyncio.get_event_loop()
    bounced_addresses = await loop.run_in_executor(None, check_bounces, 14)

    if not bounced_addresses:
        return {"bounced_found": 0, "message": "No bounces detected"}

    sends_result = await db.execute(
        select(CampaignSend, Contact.email)
        .join(Contact, CampaignSend.contact_id == Contact.id)
        .where(CampaignSend.campaign_id == campaign_id)
        .where(CampaignSend.status == "sent")
    )
    rows = sends_result.all()

    bounced_count = 0
    for send, email in rows:
        if email.lower() in [b.lower() for b in bounced_addresses]:
            send.status = "bounced"
            send.bounce_detected_at = datetime.utcnow()
            db.add(send)
            bounced_count += 1

    campaign.bounced_count = (
        await db.execute(
            select(func.count(CampaignSend.id))
            .where(CampaignSend.campaign_id == campaign_id)
            .where(CampaignSend.status == "bounced")
        )
    ).scalar()
    db.add(campaign)
    await db.commit()

    return {"bounced_found": bounced_count, "total_checked": len(rows)}


@router.get("/{campaign_id}/report/export")
async def export_campaign_report(campaign_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(CampaignSend, Contact.email, Contact.name, Contact.role, College.name.label("college_name"))
        .join(Contact, CampaignSend.contact_id == Contact.id)
        .join(College, Contact.college_id == College.id)
        .where(CampaignSend.campaign_id == campaign_id)
        .order_by(CampaignSend.status)
    )).all()

    sends_data = [
        {
            "contact_email": email,
            "contact_name": name,
            "college_name": college_name,
            "role": role,
            "status": s.status,
            "sent_at": str(s.sent_at),
            "error_message": s.error_message,
            "bounce_detected_at": str(s.bounce_detected_at),
        }
        for s, email, name, role, college_name in rows
    ]

    csv_content = campaign_report_to_csv(sends_data)
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id}_report.csv"},
    )


async def _run_campaign_send(
    campaign_id: int,
    recipients: list[dict],
    subject: str,
    template_html: str,
) -> None:
    """Background task: sends emails and updates send records."""
    async with AsyncSessionLocal() as db:
        async def on_progress(sent_so_far, total, result):
            send_result = await db.execute(
                select(CampaignSend)
                .where(CampaignSend.campaign_id == campaign_id)
                .where(CampaignSend.contact_id == result["contact_id"])
            )
            send = send_result.scalar_one_or_none()
            if send:
                send.status = "sent" if result["success"] else "failed"
                send.sent_at = datetime.utcnow()
                send.error_message = result.get("error", "")
                db.add(send)
                await db.commit()

            campaign = await db.get(Campaign, campaign_id)
            if campaign:
                if result["success"]:
                    campaign.sent_count = sent_so_far
                else:
                    campaign.failed_count = (campaign.failed_count or 0) + 1
                db.add(campaign)
                await db.commit()

        await send_bulk(recipients, subject, template_html, progress_callback=on_progress)

        campaign = await db.get(Campaign, campaign_id)
        if campaign:
            campaign.status = "sent"
            db.add(campaign)
            await db.commit()
