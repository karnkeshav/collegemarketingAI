from datetime import datetime
from sqlalchemy import (
    Integer, String, Boolean, DateTime, ForeignKey, Text, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    colleges: Mapped[list["College"]] = relationship(back_populates="state")


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"))
    city: Mapped[str] = mapped_column(String(100), default="")
    college_type: Mapped[str] = mapped_column(String(100), default="")
    streams: Mapped[str] = mapped_column(Text, default="[]")
    website: Mapped[str] = mapped_column(String(500), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    aicte_code: Mapped[str] = mapped_column(String(50), default="")
    naac_grade: Mapped[str] = mapped_column(String(10), default="")
    scrape_status: Mapped[str] = mapped_column(String(20), default="pending")
    last_scraped: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    state: Mapped["State"] = relationship(back_populates="colleges")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="college")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    college_id: Mapped[int] = mapped_column(ForeignKey("colleges.id"))
    name: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[str] = mapped_column(String(50), default="General")
    email: Mapped[str] = mapped_column(String(300), unique=True)
    department: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    validation_status: Mapped[str] = mapped_column(String(20), default="unvalidated")
    mx_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    college: Mapped["College"] = relationship(back_populates="contacts")
    sends: Mapped[list["CampaignSend"]] = relationship(back_populates="contact")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(500))
    template_html: Mapped[str] = mapped_column(Text, default="")
    template_filename: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    bounced_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)

    sends: Mapped[list["CampaignSend"]] = relationship(back_populates="campaign")


class CampaignSend(Base):
    __tablename__ = "campaign_sends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    bounce_detected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="sends")
    contact: Mapped["Contact"] = relationship(back_populates="sends")
