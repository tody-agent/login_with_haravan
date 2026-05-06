#!/usr/bin/env python3
"""Patch Customer Profile sync to use the Bitrix-matched Haravan Company ID."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


FORM_SCRIPT_NAME = "Profile - Ticket Customer Button"
SYNC_SCRIPT_NAME = "Profile - Bitrix Sync Ticket Customer"
ENV_PATHS = ("/Volumes/Data/Skills/frappe_helpdesk/.env",)

FORM_OLD = 'const synced = unwrap(await call(SYNC_METHOD, { ticket: doc.name }));'
FORM_NEW = (
    'const syncCompanyId = company.company_id || orgId || "";\n'
    '          const synced = unwrap(await call(SYNC_METHOD, { ticket: doc.name, company_id: syncCompanyId }));'
)

SERVER_OLD = (
    'orgid = first_present([ticket.get("custom_haravan_profile_orgid"), '
    'ticket.get("custom_orgid"), ticket.get("custom_org_id"), ticket.get("custom_haravan_orgid")])'
)
SERVER_NEW = (
    'orgid = first_present([frappe.form_dict.get("company_id"), frappe.form_dict.get("orgid"), '
    'frappe.form_dict.get("org_id"), ticket.get("custom_haravan_profile_orgid"), '
    'ticket.get("custom_orgid"), ticket.get("custom_org_id"), ticket.get("custom_haravan_orgid")])'
)


def load_env_files() -> dict[str, str]:
    values: dict[str, str] = {}
    for env_path in ENV_PATHS:
        path = Path(env_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


FILE_ENV = load_env_files()


def env(name: str, fallback: str | None = None) -> str:
    value = os.environ.get(name) or FILE_ENV.get(name) or (
        os.environ.get(fallback) or FILE_ENV.get(fallback, "") if fallback else ""
    )
    value = (value or "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def request_json(session: requests.Session, method: str, url: str, **kwargs):
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code >= 400:
        raise SystemExit(f"{method} {url} failed: {response.status_code} {response.text[:500]}")
    return response.json()


def resource_url(site: str, doctype: str, name: str) -> str:
    return f"{site}/api/resource/{requests.utils.quote(doctype, safe='')}/{requests.utils.quote(name, safe='')}"


def patch_once(source: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if new in source:
        return source, False
    if old not in source:
        raise SystemExit(f"Could not find expected snippet in {label}; aborting without changes.")
    return source.replace(old, new, 1), True


def main() -> int:
    site = env("HARAVAN_HELP_SITE", "SITE_HARAVAN_URL").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY", "SITE_HARAVAN_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET", "SITE_HARAVAN_API_SECRET")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_key}:{api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    backup_dir = Path("backups") / f"profile_sync_company_id_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    targets = [
        ("HD Form Script", FORM_SCRIPT_NAME, FORM_OLD, FORM_NEW),
        ("Server Script", SYNC_SCRIPT_NAME, SERVER_OLD, SERVER_NEW),
    ]
    changed: list[str] = []

    for doctype, name, old, new in targets:
        url = resource_url(site, doctype, name)
        current = request_json(session, "GET", url)["data"]
        (backup_dir / f"{doctype.replace(' ', '_')}_{name.replace(' ', '_')}_before.json").write_text(
            json.dumps(current, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        patched_script, did_change = patch_once(current.get("script") or "", old, new, name)
        if did_change:
            updated = request_json(session, "PUT", url, data=json.dumps({"script": patched_script}))["data"]
            changed.append(name)
        else:
            updated = current
        (backup_dir / f"{doctype.replace(' ', '_')}_{name.replace(' ', '_')}_after.json").write_text(
            json.dumps(updated, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json.dumps({"changed": changed, "backup_dir": str(backup_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
