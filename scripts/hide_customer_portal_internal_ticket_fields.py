#!/usr/bin/env python3
"""Hide internal HD Ticket fields from the customer portal template.

This script applies the same visibility contract as
login_with_haravan.setup.install.configure_onboarding_service_ticket_metadata
to a live Frappe site through the REST API.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from login_with_haravan.setup.install import (
    HELPDESK_ONBOARDING_SERVICE_TEMPLATE_FIELDS,
    HELPDESK_TICKET_TEMPLATE,
)


TARGET_DOCTYPE = "HD Ticket Template Field"
TARGET_PARENTTYPE = "HD Ticket Template"
TARGET_PARENTFIELD = "fields"


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def request_json(session: requests.Session, method: str, url: str, **kwargs):
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code >= 400:
        raise requests.HTTPError(
            f"{method} {url} failed: {response.status_code} {response.text[:500]}",
            response=response,
        )
    return response.json()


def resource_url(site: str, doctype: str, name: str | None = None) -> str:
    encoded_doctype = requests.utils.quote(doctype, safe="")
    url = f"{site.rstrip('/')}/api/resource/{encoded_doctype}"
    if name:
        url += "/" + requests.utils.quote(name, safe="")
    return url


def template_field_filters(fieldname: str) -> list[list[str]]:
    return [
        ["parent", "=", HELPDESK_TICKET_TEMPLATE],
        ["parenttype", "=", TARGET_PARENTTYPE],
        ["parentfield", "=", TARGET_PARENTFIELD],
        ["fieldname", "=", fieldname],
    ]


def template_field_payload(row: dict[str, object]) -> dict[str, object]:
    return {
        "required": int(row.get("required", 0) or 0),
        "hide_from_customer": int(row.get("hide_from_customer", 0) or 0),
    }


def list_template_fields(session: requests.Session, site: str, fieldname: str) -> list[dict]:
    params = {
        "filters": json.dumps(template_field_filters(fieldname)),
        "fields": json.dumps(["name", "fieldname", "required", "hide_from_customer"]),
        "limit_page_length": 10,
    }
    result = request_json(session, "GET", resource_url(site, TARGET_DOCTYPE), params=params)
    return result.get("data") or []


def update_template_field(
    session: requests.Session,
    site: str,
    docname: str,
    payload: dict[str, object],
) -> dict:
    result = request_json(
        session,
        "PUT",
        resource_url(site, TARGET_DOCTYPE, docname),
        data=json.dumps(payload),
    )
    return result.get("data") or {}


def main() -> int:
    site = env("HARAVAN_HELP_SITE").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_key}:{api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    backup_dir = Path("backups") / (
        "customer_portal_internal_fields_"
        + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    )
    backup_dir.mkdir(parents=True, exist_ok=True)

    before = {}
    after = {}
    missing = []
    changed = []

    for row in HELPDESK_ONBOARDING_SERVICE_TEMPLATE_FIELDS:
        fieldname = str(row["fieldname"])
        matches = list_template_fields(session, site, fieldname)
        before[fieldname] = matches
        if not matches:
            missing.append(fieldname)
            continue

        payload = template_field_payload(row)
        docname = matches[0]["name"]
        current = matches[0]
        needs_update = any(current.get(key) != value for key, value in payload.items())
        after[fieldname] = (
            update_template_field(session, site, docname, payload)
            if needs_update
            else current
        )
        if needs_update:
            changed.append(fieldname)

    (backup_dir / "before.json").write_text(
        json.dumps(before, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (backup_dir / "after.json").write_text(
        json.dumps(after, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if missing:
        raise SystemExit(
            "Missing HD Ticket Template Field rows: " + ", ".join(missing)
        )

    print(
        "Customer portal internal fields configured. "
        f"Changed: {', '.join(changed) if changed else 'none'}. "
        f"Backup: {backup_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
