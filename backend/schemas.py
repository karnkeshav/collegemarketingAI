from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class StateOut(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    college_count: int = 0
    contact_count: int = 0

    class Config:
        from_attributes = True


class CollegeOut(BaseModel):
    id: int
    name: str
    state_id: int
    state_name: str = ""
    city: str
    college_type: str
    streams: str
    website: str
    address: str
    aicte_code: str
    naac_grade: str
    scrape_status: str
    last_scraped: Optional[datetime]
    contact_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ContactOut(BaseModel):
    id: int
    college_id: int
    college_name: str = ""
    state_name: str = ""
    name: str
    role: str
    email: str
    department: str
    phone: str
    source_url: str
    validation_status: str
    mx_valid: bool
    is_unsubscribed: bool
    campaigns_sent: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str
    subject: str


class CampaignOut(BaseModel):
    id: int
    name: str
    subject: str
    template_filename: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime]
    total_recipients: int
    sent_count: int
    bounced_count: int
    failed_count: int

    class Config:
        from_attributes = True


class CampaignSendOut(BaseModel):
    id: int
    campaign_id: int
    contact_id: int
    contact_email: str = ""
    contact_name: str = ""
    college_name: str = ""
    status: str
    sent_at: Optional[datetime]
    error_message: str
    bounce_detected_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScrapeRequest(BaseModel):
    state_code: Optional[str] = None
    college_id: Optional[int] = None


class ValidateRequest(BaseModel):
    contact_ids: list[int]


class SendCampaignRequest(BaseModel):
    state_codes: Optional[list[str]] = None
    roles: Optional[list[str]] = None
    contact_ids: Optional[list[int]] = None


class OverviewStats(BaseModel):
    total_colleges: int
    total_contacts: int
    validated_contacts: int
    invalid_contacts: int
    total_campaigns: int
    emails_sent: int
    emails_bounced: int
    by_state: list[dict]
    by_role: list[dict]
