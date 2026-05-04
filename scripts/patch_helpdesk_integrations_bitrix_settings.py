#!/usr/bin/env python3
"""Patch Helpdesk Integrations Settings Bitrix fields on a live Frappe site.

This keeps the existing customer webhook field but relabels it clearly, then
adds a second password field for the responsible/user.get webhook.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


SETTINGS_DOCTYPE = "Helpdesk Integrations Settings"

CUSTOM_FIELDS = [
    {
        "dt": SETTINGS_DOCTYPE,
        "fieldname": "bitrix_responsible_api_section",
        "label": "Bitrix - Responsible API (user.get)",
        "fieldtype": "Section Break",
        "insert_after": "bitrix_webhook_url",
        "collapsible": 0,
    },
    {
        "dt": SETTINGS_DOCTYPE,
        "fieldname": "bitrix_responsible_webhook_url",
        "label": "Bitrix Responsible Inbound Webhook URL",
        "fieldtype": "Password",
        "insert_after": "bitrix_responsible_api_section",
        "description": (
            "Responsible/user API. Dung de goi user.get theo ASSIGNED_BY_ID va cap nhat "
            "HD Ticket.custom_responsible khi ACTIVE=true. Tao inbound webhook rieng trong "
            "Bitrix24 voi scope user_basic. Co the nhap base webhook .../rest/57792/secret/ "
            "hoac full template .../user.get.json?ID={ASSIGNED_BY_ID}."
        ),
    },
]

FIELD_PROPERTY_PATCHES = [
    {
        "fieldname": "bitrix_enabled",
        "label": "Bitrix Enabled",
        "description": "Bat/tat lay Customer Profile va Responsible tu Bitrix.",
    },
    {
        "fieldname": "bitrix_webhook_url",
        "label": "Bitrix Customer Inbound Webhook URL",
        "description": (
            "Customer/company API. Dung de goi crm.company.* lay ho so khach hang. "
            "Tao trong Bitrix24 > Applications > Developer resources > Inbound webhook "
            "voi scope crm. Vi du: https://haravan.bitrix24.vn/rest/57792/{customer_secret_key}/"
        ),
    },
]


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


def get_doc(session: requests.Session, site: str, doctype: str, name: str) -> dict | None:
    try:
        return request_json(session, "GET", resource_url(site, doctype, name))["data"]
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def upsert_doc(session: requests.Session, site: str, doctype: str, name: str, payload: dict) -> dict:
    if get_doc(session, site, doctype, name):
        return request_json(session, "PUT", resource_url(site, doctype, name), data=json.dumps(payload))["data"]
    payload = dict(payload)
    payload["doctype"] = doctype
    payload["name"] = name
    return request_json(session, "POST", resource_url(site, doctype), data=json.dumps(payload))["data"]


def custom_field_name(fieldname: str) -> str:
    return f"{SETTINGS_DOCTYPE}-{fieldname}"


def property_setter_name(fieldname: str, prop: str) -> str:
    return f"{SETTINGS_DOCTYPE}-{fieldname}-{prop}"


def patch_existing_field_properties(session: requests.Session, site: str) -> list[str]:
    changed: list[str] = []
    for patch in FIELD_PROPERTY_PATCHES:
        fieldname = patch["fieldname"]
        custom_field = get_doc(session, site, "Custom Field", custom_field_name(fieldname))
        if custom_field:
            payload = {
                "label": patch["label"],
                "description": patch["description"],
            }
            upsert_doc(session, site, "Custom Field", custom_field_name(fieldname), payload)
            changed.append(custom_field_name(fieldname))
            continue

        for prop in ("label", "description"):
            name = property_setter_name(fieldname, prop)
            payload = {
                "doc_type": SETTINGS_DOCTYPE,
                "doctype_or_field": "DocField",
                "field_name": fieldname,
                "property": prop,
                "property_type": "Text",
                "value": patch[prop],
            }
            upsert_doc(session, site, "Property Setter", name, payload)
            changed.append(name)
    return changed


def ensure_custom_fields(session: requests.Session, site: str) -> list[str]:
    changed: list[str] = []
    for field in CUSTOM_FIELDS:
        name = custom_field_name(field["fieldname"])
        payload = dict(field)
        payload["name"] = name
        upsert_doc(session, site, "Custom Field", name, payload)
        changed.append(name)
    return changed


def fetch_settings_doc(session: requests.Session, site: str) -> dict:
    return request_json(session, "GET", resource_url(site, SETTINGS_DOCTYPE, SETTINGS_DOCTYPE))["data"]


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
        "helpdesk_integrations_bitrix_settings_"
        + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    )
    backup_dir.mkdir(parents=True, exist_ok=True)
    before = fetch_settings_doc(session, site)
    (backup_dir / "settings_before.json").write_text(
        json.dumps(before, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    property_changes = patch_existing_field_properties(session, site)
    custom_field_changes = ensure_custom_fields(session, site)

    after = fetch_settings_doc(session, site)
    (backup_dir / "settings_after.json").write_text(
        json.dumps(after, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        "Helpdesk Integrations Settings Bitrix fields patched. "
        f"Properties: {', '.join(property_changes)}. "
        f"Custom fields: {', '.join(custom_field_changes)}. "
        f"Backup: {backup_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
