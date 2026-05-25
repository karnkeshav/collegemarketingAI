"""
Validates email addresses using:
1. Syntax check (email-validator library)
2. DNS/MX record lookup (dnspython)
"""
import asyncio
import logging

import dns.resolver
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)


async def validate_email_address(email: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason).
    is_valid=True only when syntax AND MX record both pass.
    """
    email = email.strip().lower()

    # 1. Syntax check
    try:
        result = validate_email(email, check_deliverability=False)
        email = result.normalized
    except EmailNotValidError as e:
        return False, f"syntax: {e}"

    # 2. MX record check
    domain = email.split("@")[1]
    try:
        loop = asyncio.get_event_loop()
        mx_valid = await loop.run_in_executor(None, _check_mx, domain)
        if not mx_valid:
            return False, "no MX record"
    except Exception as e:
        return False, f"dns error: {e}"

    return True, "valid"


def _check_mx(domain: str) -> bool:
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(answers) > 0
    except Exception:
        try:
            dns.resolver.resolve(domain, "A", lifetime=5)
            return True
        except Exception:
            return False


async def batch_validate(emails: list[str]) -> dict[str, tuple[bool, str]]:
    """Validate a list of emails concurrently (max 20 at a time)."""
    semaphore = asyncio.Semaphore(20)

    async def _validate_one(email: str):
        async with semaphore:
            return email, await validate_email_address(email)

    tasks = [_validate_one(e) for e in emails]
    results = await asyncio.gather(*tasks)
    return dict(results)
