#!/usr/bin/env python3
"""Patch GitLab popup scripts to default labels from Product Suggestion.

The live Helpdesk GitLab popup is managed as Desk records:
- HD Form Script: GitLab - Ticket Issue Button
- Server Script: GitLab - Ticket Issue API

This script fetches the records, writes backups, applies idempotent narrow
patches, validates the JavaScript body, and updates the records by REST API.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


HD_FORM_SCRIPT_NAMES = ["GitLab - Ticket Issue Button", "HD Ticket - GitLab Popup V3"]
SERVER_SCRIPT_NAMES = ["GitLab - Ticket Issue API", "HD GitLab Popup API v2"]
BASE_GITLAB_LABELS = "helpdesk,customer-report"


SERVER_HELPERS = r'''
PRODUCT_SUGGESTION_DOCTYPE = "HD Ticket Product Suggestion"
PRODUCT_SUGGESTION_FIELD = "custom_product_suggestion"
PRODUCT_SUGGESTION_LABEL_FIELD = "gitlab_labels"
BASE_GITLAB_LABELS = "helpdesk,customer-report"
'''


SERVER_LABEL_FUNCTIONS = r'''

def split_labels(value):
    labels = []
    for raw in as_text(value).replace("\n", ",").replace(";", ",").split(","):
        label = as_text(raw)
        if label and label not in labels:
            labels.append(label)
    return labels


def product_suggestion_labels(ticket_name):
    suggestion = as_text(frappe.db.get_value(TICKET_DTYPE, ticket_name, PRODUCT_SUGGESTION_FIELD))
    if not suggestion:
        return []
    try:
        raw_labels = frappe.db.get_value(PRODUCT_SUGGESTION_DOCTYPE, suggestion, PRODUCT_SUGGESTION_LABEL_FIELD)
    except Exception as exc:
        frappe.log_error("GitLab product suggestion label lookup failed: " + as_text(exc)[:800], "HD GitLab Labels")
        return []
    return split_labels(raw_labels)


def gitlab_default_labels(ticket_name):
    labels = split_labels(BASE_GITLAB_LABELS)
    for label in product_suggestion_labels(ticket_name):
        if label not in labels:
            labels.append(label)
    return ",".join(labels)
'''


def patch_server_script(script: str) -> str:
    patched = script

    if "PRODUCT_SUGGESTION_DOCTYPE" not in patched:
        patched = patched.replace('TICKET_DTYPE = "HD Ticket"\n', 'TICKET_DTYPE = "HD Ticket"\n' + SERVER_HELPERS)

    if "def split_labels(value):" not in patched:
        patched = patched.replace("\ndef get_tracker_by_ticket(ticket_name):\n", SERVER_LABEL_FUNCTIONS + "\n\ndef get_tracker_by_ticket(ticket_name):\n")

    if '"custom_product_suggestion"' not in patched:
        patched = patched.replace(
            '        "status": ticket.get("status") or "",\n',
            '        "status": ticket.get("status") or "",\n'
            '        "custom_product_suggestion": ticket.get("custom_product_suggestion") or "",\n',
        )

    old_init = (
        '    frappe.response["message"] = {"ok": True, "linked": linked, "ticket": ticket_payload(ticket_name), '
        '"tracker": tracker.name if tracker else None, "issue": issue, "comments": comments, '
        '"project_id": project_id, "project_path": gitlab_project_path()}'
    )
    new_init = (
        '    frappe.response["message"] = {"ok": True, "linked": linked, "ticket": ticket_payload(ticket_name), '
        '"tracker": tracker.name if tracker else None, "issue": issue, "comments": comments, '
        '"project_id": project_id, "project_path": gitlab_project_path(), '
        '"default_labels": gitlab_default_labels(ticket_name)}'
    )
    patched = patched.replace(old_init, new_init)

    patched = patched.replace(
        '    labels = as_text(frappe.form_dict.get("labels") or "helpdesk,customer-report")\n',
        '    labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name) or BASE_GITLAB_LABELS)\n',
    )

    required = [
        "PRODUCT_SUGGESTION_DOCTYPE",
        "def gitlab_default_labels(ticket_name):",
        '"default_labels": gitlab_default_labels(ticket_name)',
        "gitlab_default_labels(ticket_name) or BASE_GITLAB_LABELS",
    ]
    missing = [text for text in required if text not in patched]
    if missing:
        raise ValueError("Server script patch did not apply cleanly: " + ", ".join(missing))

    return patched


def patch_form_script(script: str) -> str:
    patched = script

    if "const defLabels =" not in patched:
        patched = patched.replace(
            "        const defDesc = plainText(ticket.description || doc.description || doc.content || '');\n",
            "        const defDesc = plainText(ticket.description || doc.description || doc.content || '');\n"
            "        const defLabels = init.default_labels || 'helpdesk,customer-report';\n",
        )

    patched = patched.replace(
        "                        labels: document.getElementById(`${id}-labels`)?.value || 'helpdesk,customer-report'\n",
        "                        labels: document.getElementById(`${id}-labels`)?.value || defLabels\n",
    )
    patched = patched.replace(
        '                                value="helpdesk,customer-report"\n',
        '                                value="${esc(defLabels)}"\n',
    )

    required = [
        "const defLabels = init.default_labels || 'helpdesk,customer-report';",
        "labels: document.getElementById(`${id}-labels`)?.value || defLabels",
        'value="${esc(defLabels)}"',
    ]
    missing = [text for text in required if text not in patched]
    if missing:
        raise ValueError("Form script patch did not apply cleanly: " + ", ".join(missing))

    return patched


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def request_json(session: requests.Session, method: str, url: str, **kwargs):
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code >= 400:
        raise requests.HTTPError(f"{method} {url} failed: {response.status_code} {response.text[:500]}", response=response)
    return response.json()


def fetch_first_doc(session: requests.Session, site: str, doctype: str, names: list[str]) -> tuple[str, dict]:
    for name in names:
        encoded_doctype = requests.utils.quote(doctype, safe="")
        encoded_name = requests.utils.quote(name, safe="")
        url = f"{site}/api/resource/{encoded_doctype}/{encoded_name}"
        try:
            return name, request_json(session, "GET", url)["data"]
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                continue
            raise
    raise SystemExit(f"Could not find {doctype}: {', '.join(names)}")


def update_doc(session: requests.Session, site: str, doctype: str, name: str, payload: dict) -> dict:
    encoded_doctype = requests.utils.quote(doctype, safe="")
    encoded_name = requests.utils.quote(name, safe="")
    url = f"{site}/api/resource/{encoded_doctype}/{encoded_name}"
    return request_json(session, "PUT", url, data=json.dumps(payload))["data"]


def validate_javascript(script: str) -> None:
    subprocess.run(["node", "-e", f"new Function({json.dumps(script)});"], check=True)


def main() -> int:
    site = env("HARAVAN_HELP_SITE").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {api_key}:{api_secret}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })

    backup_dir = Path("backups") / f"gitlab_product_labels_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    form_name, form_doc = fetch_first_doc(session, site, "HD Form Script", HD_FORM_SCRIPT_NAMES)
    server_name, server_doc = fetch_first_doc(session, site, "Server Script", SERVER_SCRIPT_NAMES)

    (backup_dir / "hd_form_script_before.json").write_text(json.dumps(form_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (backup_dir / "server_script_before.json").write_text(json.dumps(server_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    patched_form = patch_form_script(form_doc.get("script") or "")
    patched_server = patch_server_script(server_doc.get("script") or "")
    validate_javascript(patched_form)

    updated_form = update_doc(session, site, "HD Form Script", form_name, {"script": patched_form, "enabled": 1})
    updated_server = update_doc(session, site, "Server Script", server_name, {"script": patched_server, "disabled": 0})

    (backup_dir / "hd_form_script_after.json").write_text(json.dumps(updated_form, ensure_ascii=False, indent=2), encoding="utf-8")
    (backup_dir / "server_script_after.json").write_text(json.dumps(updated_server, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Patched {form_name} and {server_name}. Backup: {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
