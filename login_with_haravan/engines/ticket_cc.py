"""Ticket-level CC email normalization and merge helpers."""

from __future__ import annotations

import re
from email.utils import parseaddr
from typing import Iterable


TICKET_CC_FIELD = "custom_cc_emails"

_EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")


class InvalidCCEmailError(ValueError):
    """Raised when one or more CC email values are invalid."""

    def __init__(self, invalid_emails: list[str]):
        self.invalid_emails = invalid_emails
        super().__init__("Invalid CC email(s): " + ", ".join(invalid_emails))


def _iter_tokens(value) -> Iterable[str]:
    if not value:
        return []
    if isinstance(value, str):
        normalized = value.replace(";", ",").replace("\n", ",")
        return [item.strip() for item in normalized.split(",")]
    if isinstance(value, (list, tuple, set)):
        return [str(item or "").strip() for item in value]
    return [str(value).strip()]


def _normalize_email(token: str) -> str | None:
    token = str(token or "").strip()
    if not token:
        return None

    _, address = parseaddr(token)
    address = (address or token).strip().lower()
    if not _EMAIL_RE.match(address):
        return None
    return address


def parse_cc_emails(value) -> list[str]:
    """Parse, validate, lowercase, and de-duplicate CC email input."""
    emails: list[str] = []
    seen: set[str] = set()
    invalid: list[str] = []

    for token in _iter_tokens(value):
        if not token:
            continue
        email = _normalize_email(token)
        if not email:
            invalid.append(token)
            continue
        if email in seen:
            continue
        seen.add(email)
        emails.append(email)

    if invalid:
        raise InvalidCCEmailError(invalid)

    return emails


def normalize_cc_email_text(value) -> str:
    return ", ".join(parse_cc_emails(value))


def _parse_valid_email_set(value) -> set[str]:
    emails: set[str] = set()
    for token in _iter_tokens(value):
        email = _normalize_email(token)
        if email:
            emails.add(email)
    return emails


def merge_cc_emails(ticket_cc=None, existing_cc=None, recipients=None) -> list[str]:
    """Merge existing CC with ticket-level CC, excluding primary recipients."""
    excluded = _parse_valid_email_set(recipients)
    merged: list[str] = []
    seen: set[str] = set()

    for source in (existing_cc, ticket_cc):
        for email in parse_cc_emails(source):
            if email in excluded or email in seen:
                continue
            seen.add(email)
            merged.append(email)

    return merged


def merge_cc_email_text(ticket_cc=None, existing_cc=None, recipients=None) -> str:
    return ", ".join(merge_cc_emails(ticket_cc, existing_cc, recipients))


def validate_ticket_cc_emails(doc, method=None):
    """Frappe doc hook: normalize or reject HD Ticket CC emails."""
    raw_value = getattr(doc, TICKET_CC_FIELD, None)
    if not raw_value:
        return

    try:
        normalized = normalize_cc_email_text(raw_value)
    except InvalidCCEmailError as exc:
        import frappe

        frappe.throw("Invalid CC Emails: " + ", ".join(exc.invalid_emails))
        return

    setattr(doc, TICKET_CC_FIELD, normalized)
