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
PRODUCT_SUGGESTION_ASSIGN_FIELD = "assign_to"
PRODUCT_SUGGESTION_PROJECT_ID_FIELD = "default_gitlab_projectid"
TICKET_INTERNAL_TYPE_FIELDS = ["custom_internal_type", "ticket_type"]
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


def ticket_internal_type(ticket_name):
    for fieldname in TICKET_INTERNAL_TYPE_FIELDS:
        value = as_text(frappe.db.get_value(TICKET_DTYPE, ticket_name, fieldname))
        if value:
            return value
    return ""


def internal_type_labels(ticket_name):
    value = ticket_internal_type(ticket_name).lower()
    if value == "system bug / incident":
        return ["Bug"]
    if value == "technical support":
        return ["Support"]
    if value == "api support":
        return ["API_Support"]
    return []


def gitlab_default_labels(ticket_name):
    labels = []
    for label in product_suggestion_labels(ticket_name) + internal_type_labels(ticket_name):
        if label not in labels:
            labels.append(label)
    return ",".join(labels)


def product_suggestion_value(ticket_name, fieldname):
    suggestion = as_text(frappe.db.get_value(TICKET_DTYPE, ticket_name, PRODUCT_SUGGESTION_FIELD))
    if not suggestion:
        return ""
    try:
        return as_text(frappe.db.get_value(PRODUCT_SUGGESTION_DOCTYPE, suggestion, fieldname))
    except Exception as exc:
        frappe.log_error("GitLab product suggestion lookup failed: " + as_text(exc)[:800], "HD GitLab Defaults")
        return ""


def gitlab_default_assignee_ids(ticket_name):
    assignees = []
    for value in split_labels(product_suggestion_value(ticket_name, PRODUCT_SUGGESTION_ASSIGN_FIELD)):
        if value.isdigit() and value not in assignees:
            assignees.append(value)
    return ",".join(assignees)


def gitlab_default_project_id(ticket_name):
    project_id = product_suggestion_value(ticket_name, PRODUCT_SUGGESTION_PROJECT_ID_FIELD)
    if project_id and project_id.isdigit():
        return project_id
    return ""
'''


def patch_server_script(script: str) -> str:
    patched = script

    if "PRODUCT_SUGGESTION_DOCTYPE" not in patched:
        patched = patched.replace('TICKET_DTYPE = "HD Ticket"\n', 'TICKET_DTYPE = "HD Ticket"\n' + SERVER_HELPERS)
    elif "PRODUCT_SUGGESTION_ASSIGN_FIELD" not in patched:
        patched = patched.replace(
            'PRODUCT_SUGGESTION_LABEL_FIELD = "gitlab_labels"\n',
            'PRODUCT_SUGGESTION_LABEL_FIELD = "gitlab_labels"\n'
            'PRODUCT_SUGGESTION_ASSIGN_FIELD = "assign_to"\n'
            'PRODUCT_SUGGESTION_PROJECT_ID_FIELD = "default_gitlab_projectid"\n',
        )
    if "TICKET_INTERNAL_TYPE_FIELDS" not in patched:
        patched = patched.replace(
            'PRODUCT_SUGGESTION_PROJECT_ID_FIELD = "default_gitlab_projectid"\n',
            'PRODUCT_SUGGESTION_PROJECT_ID_FIELD = "default_gitlab_projectid"\n'
            'TICKET_INTERNAL_TYPE_FIELDS = ["custom_internal_type", "ticket_type"]\n',
        )

    if "def split_labels(value):" not in patched:
        patched = patched.replace("\ndef get_tracker_by_ticket(ticket_name):\n", SERVER_LABEL_FUNCTIONS + "\n\ndef get_tracker_by_ticket(ticket_name):\n")
    elif "def gitlab_default_assignee_ids(ticket_name):" not in patched:
        patched = patched.replace(
            'def gitlab_default_labels(ticket_name):\n'
            '    return ",".join(product_suggestion_labels(ticket_name))\n',
            'def gitlab_default_labels(ticket_name):\n'
            '    return ",".join(product_suggestion_labels(ticket_name))\n'
            '\n'
            '\n'
            'def product_suggestion_value(ticket_name, fieldname):\n'
            '    suggestion = as_text(frappe.db.get_value(TICKET_DTYPE, ticket_name, PRODUCT_SUGGESTION_FIELD))\n'
            '    if not suggestion:\n'
            '        return ""\n'
            '    try:\n'
            '        return as_text(frappe.db.get_value(PRODUCT_SUGGESTION_DOCTYPE, suggestion, fieldname))\n'
            '    except Exception as exc:\n'
            '        frappe.log_error("GitLab product suggestion lookup failed: " + as_text(exc)[:800], "HD GitLab Defaults")\n'
            '        return ""\n'
            '\n'
            '\n'
            'def gitlab_default_assignee_ids(ticket_name):\n'
            '    assignees = []\n'
            '    for value in split_labels(product_suggestion_value(ticket_name, PRODUCT_SUGGESTION_ASSIGN_FIELD)):\n'
            '        if value.isdigit() and value not in assignees:\n'
            '            assignees.append(value)\n'
            '    return ",".join(assignees)\n'
            '\n'
            '\n'
            'def gitlab_default_project_id(ticket_name):\n'
            '    project_id = product_suggestion_value(ticket_name, PRODUCT_SUGGESTION_PROJECT_ID_FIELD)\n'
            '    if project_id and project_id.isdigit():\n'
            '        return project_id\n'
            '    return ""\n',
        )

    if "def internal_type_labels(ticket_name):" not in patched:
        patched = patched.replace(
            'def gitlab_default_labels(ticket_name):\n'
            '    return ",".join(product_suggestion_labels(ticket_name))\n',
            'def ticket_internal_type(ticket_name):\n'
            '    for fieldname in TICKET_INTERNAL_TYPE_FIELDS:\n'
            '        value = as_text(frappe.db.get_value(TICKET_DTYPE, ticket_name, fieldname))\n'
            '        if value:\n'
            '            return value\n'
            '    return ""\n'
            '\n'
            '\n'
            'def internal_type_labels(ticket_name):\n'
            '    value = ticket_internal_type(ticket_name).lower()\n'
            '    if value == "system bug / incident":\n'
            '        return ["Bug"]\n'
            '    if value == "technical support":\n'
            '        return ["Support"]\n'
            '    if value == "api support":\n'
            '        return ["API_Support"]\n'
            '    return []\n'
            '\n'
            '\n'
            'def gitlab_default_labels(ticket_name):\n'
            '    labels = []\n'
            '    for label in product_suggestion_labels(ticket_name) + internal_type_labels(ticket_name):\n'
            '        if label not in labels:\n'
            '            labels.append(label)\n'
            '    return ",".join(labels)\n',
        )
    else:
        patched = patched.replace(
            'def gitlab_default_labels(ticket_name):\n'
            '    return ",".join(product_suggestion_labels(ticket_name))\n',
            'def gitlab_default_labels(ticket_name):\n'
            '    labels = []\n'
            '    for label in product_suggestion_labels(ticket_name) + internal_type_labels(ticket_name):\n'
            '        if label not in labels:\n'
            '            labels.append(label)\n'
            '    return ",".join(labels)\n',
        )

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
        '"default_labels": gitlab_default_labels(ticket_name), '
        '"default_assignee_ids": gitlab_default_assignee_ids(ticket_name), '
        '"default_project_id": gitlab_default_project_id(ticket_name)}'
    )
    patched = patched.replace(old_init, new_init)
    patched = patched.replace(
        '"project_id": project_id, "project_path": gitlab_project_path(), "default_labels": gitlab_default_labels(ticket_name)}',
        '"project_id": project_id, "project_path": gitlab_project_path(), "default_labels": gitlab_default_labels(ticket_name), '
        '"default_assignee_ids": gitlab_default_assignee_ids(ticket_name), "default_project_id": gitlab_default_project_id(ticket_name)}',
    )

    patched = patched.replace(
        '    labels = as_text(frappe.form_dict.get("labels") or "helpdesk,customer-report")\n',
        '    labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name))\n',
    )
    patched = patched.replace(
        '    labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name) or BASE_GITLAB_LABELS)\n',
        '    labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name))\n',
    )
    if "create_project_id = as_text(" not in patched:
        patched = patched.replace(
            '    labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name))\n',
            '    labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name))\n'
            '    create_project_id = as_text(frappe.form_dict.get("project_id") or gitlab_default_project_id(ticket_name) or project_id)\n'
            '    assignee_ids = []\n'
            '    for assignee_id in split_labels(frappe.form_dict.get("assignee_ids") or gitlab_default_assignee_ids(ticket_name)):\n'
            '        if assignee_id.isdigit() and assignee_id not in assignee_ids:\n'
            '            assignee_ids.append(assignee_id)\n',
        )
    patched = patched.replace(
        'def gitlab_default_labels(ticket_name):\n'
        '    labels = split_labels(BASE_GITLAB_LABELS)\n'
        '    for label in product_suggestion_labels(ticket_name):\n'
        '        if label not in labels:\n'
        '            labels.append(label)\n'
        '    return ",".join(labels)\n',
        'def gitlab_default_labels(ticket_name):\n'
        '    return ",".join(product_suggestion_labels(ticket_name))\n',
    )
    if "create_payload =" not in patched:
        patched = patched.replace(
            '    issue = api_post("/projects/" + project_id + "/issues", {"title": title, "description": full_description, "labels": labels})\n',
            '    create_payload = {"title": title, "description": full_description, "labels": labels}\n'
            '    if assignee_ids:\n'
            '        create_payload["assignee_ids"] = [int(value) for value in assignee_ids]\n'
            '    issue = api_post("/projects/" + create_project_id + "/issues", create_payload)\n',
        )

    required = [
        "PRODUCT_SUGGESTION_DOCTYPE",
        "PRODUCT_SUGGESTION_ASSIGN_FIELD",
        "PRODUCT_SUGGESTION_PROJECT_ID_FIELD",
        "TICKET_INTERNAL_TYPE_FIELDS",
        "def gitlab_default_labels(ticket_name):",
        "def internal_type_labels(ticket_name):",
        'return ["Bug"]',
        'return ["Support"]',
        'return ["API_Support"]',
        "product_suggestion_labels(ticket_name) + internal_type_labels(ticket_name)",
        "def gitlab_default_assignee_ids(ticket_name):",
        "def gitlab_default_project_id(ticket_name):",
        '"default_labels": gitlab_default_labels(ticket_name)',
        '"default_assignee_ids": gitlab_default_assignee_ids(ticket_name)',
        '"default_project_id": gitlab_default_project_id(ticket_name)',
        'frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name)',
        'create_project_id = as_text(frappe.form_dict.get("project_id") or gitlab_default_project_id(ticket_name) or project_id)',
        'create_payload["assignee_ids"] = [int(value) for value in assignee_ids]',
        'api_post("/projects/" + create_project_id + "/issues", create_payload)',
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
            "        const defLabels = init.default_labels || '';\n",
        )
    if "const defAssigneeIds =" not in patched:
        patched = patched.replace(
            "        const defLabels = init.default_labels || '';\n",
            "        const defLabels = init.default_labels || '';\n"
            "        const defAssigneeIds = init.default_assignee_ids || '';\n"
            "        const defProjectId = init.default_project_id || '';\n",
        )

    patched = patched.replace(
        "                        labels: document.getElementById(`${id}-labels`)?.value || 'helpdesk,customer-report'\n",
        "                        labels: document.getElementById(`${id}-labels`)?.value || defLabels,\n"
        "                        assignee_ids: document.getElementById(`${id}-assignee-ids`)?.value || defAssigneeIds,\n"
        "                        project_id: document.getElementById(`${id}-project-id`)?.value || defProjectId\n",
    )
    if "assignee_ids: document.getElementById(`${id}-assignee-ids`)?.value || defAssigneeIds" not in patched:
        patched = patched.replace(
            "                        labels: document.getElementById(`${id}-labels`)?.value || defLabels\n",
            "                        labels: document.getElementById(`${id}-labels`)?.value || defLabels,\n"
            "                        assignee_ids: document.getElementById(`${id}-assignee-ids`)?.value || defAssigneeIds,\n"
            "                        project_id: document.getElementById(`${id}-project-id`)?.value || defProjectId\n",
        )
    patched = patched.replace(
        '                                value="helpdesk,customer-report"\n',
        '                                value="${esc(defLabels)}"\n',
    )
    if 'id="${id}-assignee-ids"' not in patched:
        patched = patched.replace(
            '                            <input id="${id}-labels" class="gl-input" type="text"\n'
            '                                value="${esc(defLabels)}"\n'
            '                                placeholder="Labels phân cách bởi dấu phẩy">\n',
            '                            <input id="${id}-labels" class="gl-input" type="text"\n'
            '                                value="${esc(defLabels)}"\n'
            '                                placeholder="Labels phân cách bởi dấu phẩy">\n'
            '                            <label class="gl-label" for="${id}-assignee-ids">Assignee IDs</label>\n'
            '                            <input id="${id}-assignee-ids" class="gl-input" type="text"\n'
            '                                value="${esc(defAssigneeIds)}"\n'
            '                                placeholder="GitLab user ID, phân cách bởi dấu phẩy">\n'
            '                            <label class="gl-label" for="${id}-project-id">Project ID</label>\n'
            '                            <input id="${id}-project-id" class="gl-input" type="text"\n'
            '                                value="${esc(defProjectId)}"\n'
            '                                placeholder="Để trống để dùng cấu hình mặc định">\n',
        )
    patched = patched.replace(
        "        const defLabels = init.default_labels || 'helpdesk,customer-report';\n",
        "        const defLabels = init.default_labels || '';\n"
        "        const defAssigneeIds = init.default_assignee_ids || '';\n"
        "        const defProjectId = init.default_project_id || '';\n",
    )

    required = [
        "const defLabels = init.default_labels || '';",
        "const defAssigneeIds = init.default_assignee_ids || '';",
        "const defProjectId = init.default_project_id || '';",
        "labels: document.getElementById(`${id}-labels`)?.value || defLabels",
        "assignee_ids: document.getElementById(`${id}-assignee-ids`)?.value || defAssigneeIds",
        "project_id: document.getElementById(`${id}-project-id`)?.value || defProjectId",
        'value="${esc(defLabels)}"',
        'value="${esc(defAssigneeIds)}"',
        'value="${esc(defProjectId)}"',
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
