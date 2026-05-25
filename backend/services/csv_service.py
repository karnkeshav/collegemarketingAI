import csv
import io
from datetime import datetime
from typing import Optional


def contacts_to_csv(contacts: list[dict]) -> str:
    """Convert a list of contact dicts to CSV string."""
    fieldnames = [
        "id", "college_name", "state", "city", "college_type",
        "contact_name", "role", "department", "email", "phone",
        "validation_status", "source_url", "created_at",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for c in contacts:
        row = {
            "id": c.get("id", ""),
            "college_name": c.get("college_name", ""),
            "state": c.get("state_name", ""),
            "city": c.get("city", ""),
            "college_type": c.get("college_type", ""),
            "contact_name": c.get("name", ""),
            "role": c.get("role", ""),
            "department": c.get("department", ""),
            "email": c.get("email", ""),
            "phone": c.get("phone", ""),
            "validation_status": c.get("validation_status", ""),
            "source_url": c.get("source_url", ""),
            "created_at": c.get("created_at", ""),
        }
        writer.writerow(row)

    return output.getvalue()


def campaign_report_to_csv(sends: list[dict]) -> str:
    """Convert campaign send records to CSV."""
    fieldnames = [
        "contact_email", "contact_name", "college_name", "role",
        "status", "sent_at", "error_message", "bounce_detected_at",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for s in sends:
        writer.writerow({
            "contact_email": s.get("contact_email", ""),
            "contact_name": s.get("contact_name", ""),
            "college_name": s.get("college_name", ""),
            "role": s.get("role", ""),
            "status": s.get("status", ""),
            "sent_at": s.get("sent_at", ""),
            "error_message": s.get("error_message", ""),
            "bounce_detected_at": s.get("bounce_detected_at", ""),
        })

    return output.getvalue()
