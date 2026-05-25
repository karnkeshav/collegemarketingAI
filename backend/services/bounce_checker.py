"""
Polls Gmail inbox via IMAP to detect bounce-back (NDR) emails
and returns the recipient addresses that bounced.
"""
import email as email_lib
import logging
import re
from typing import Optional

import imapclient

from config import settings

logger = logging.getLogger(__name__)

NDR_SUBJECTS = [
    "delivery status notification",
    "delivery failed",
    "mail delivery failed",
    "mail delivery failure",
    "undelivered mail",
    "returned mail",
    "failure notice",
    "message not delivered",
    "address not found",
]

NDR_SENDERS = [
    "mailer-daemon",
    "postmaster",
    "mail delivery subsystem",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def check_bounces(since_days: int = 7) -> list[str]:
    """
    Connects to Gmail IMAP and returns a list of bounced email addresses
    detected in the last `since_days` days.
    """
    if not settings.gmail_app_password:
        logger.warning("Gmail App Password not configured — bounce check skipped")
        return []

    bounced = set()
    try:
        client = imapclient.IMAPClient("imap.gmail.com", ssl=True)
        client.login(settings.gmail_user, settings.gmail_app_password)
        client.select_folder("INBOX")

        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(days=since_days)).date()

        messages = client.search(["SINCE", since_date])
        if not messages:
            client.logout()
            return []

        fetched = client.fetch(messages, ["ENVELOPE", "RFC822.TEXT", "RFC822.HEADER"])
        for uid, data in fetched.items():
            subject = ""
            sender = ""
            try:
                envelope = data.get(b"ENVELOPE")
                if envelope:
                    subject = (envelope.subject or b"").decode("utf-8", errors="ignore").lower()
                    if envelope.from_:
                        f = envelope.from_[0]
                        sender = (
                            (f.mailbox or b"").decode("utf-8", errors="ignore") + "@" +
                            (f.host or b"").decode("utf-8", errors="ignore")
                        ).lower()

                is_ndr = (
                    any(kw in subject for kw in NDR_SUBJECTS)
                    or any(kw in sender for kw in NDR_SENDERS)
                )

                if is_ndr:
                    body = data.get(b"RFC822.TEXT", b"").decode("utf-8", errors="ignore")
                    header = data.get(b"RFC822.HEADER", b"").decode("utf-8", errors="ignore")
                    full_text = body + " " + header

                    for match in EMAIL_RE.finditer(full_text):
                        addr = match.group(0).lower()
                        # Skip system addresses
                        if not any(s in addr for s in ["mailer-daemon", "postmaster", "noreply"]):
                            bounced.add(addr)

            except Exception as e:
                logger.debug(f"Error parsing message {uid}: {e}")
                continue

        client.logout()
    except Exception as e:
        logger.error(f"IMAP connection failed: {e}")

    return list(bounced)
