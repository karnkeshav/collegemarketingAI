"""
Gmail SMTP email sender.
Uses App Password authentication with 2-second per-email delay
to stay within Gmail's ~500 emails/day limit.
"""
import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    to_name: str = "",
) -> tuple[bool, str]:
    """
    Send a single email via Gmail SMTP.
    Returns (success, error_message).
    """
    if not settings.gmail_app_password:
        return False, "Gmail App Password not configured in .env"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"CollegeMarketing <{settings.gmail_user}>"
        msg["To"] = f"{to_name} <{to_email}>" if to_name else to_email

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _smtp_send, msg, to_email)
        return True, ""
    except Exception as e:
        logger.error(f"Send failed to {to_email}: {e}")
        return False, str(e)


def _smtp_send(msg: MIMEMultipart, to_email: str) -> None:
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(settings.gmail_user, settings.gmail_app_password)
        server.sendmail(settings.gmail_user, to_email, msg.as_string())


async def send_bulk(
    recipients: list[dict],
    subject: str,
    html_template: str,
    progress_callback=None,
) -> list[dict]:
    """
    Send to a list of recipients with 2s delay between each.
    recipients: [{"email": ..., "name": ..., "contact_id": ...}, ...]
    Returns list of result dicts with status per recipient.
    """
    results = []
    for i, recipient in enumerate(recipients):
        success, error = await send_email(
            to_email=recipient["email"],
            subject=subject,
            html_body=html_template,
            to_name=recipient.get("name", ""),
        )
        result = {
            "contact_id": recipient["contact_id"],
            "email": recipient["email"],
            "success": success,
            "error": error,
        }
        results.append(result)

        if progress_callback:
            await progress_callback(i + 1, len(recipients), result)

        await asyncio.sleep(2)

    return results
