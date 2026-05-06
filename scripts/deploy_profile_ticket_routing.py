#!/usr/bin/env python3
"""Deploy the Desk-managed HD Ticket customer-segment routing Server Script."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


SERVER_SCRIPT_NAME = "Profile - Ticket Routing"
ASSIGNMENT_SERVER_SCRIPT_NAME = "Profile - Ticket Round Robin Assignment"
REFERENCE_DOCTYPE = "HD Ticket"
DOCTYPE_EVENT = "Before Insert"
ASSIGNMENT_DOCTYPE_EVENT = "After Insert"


SERVER_SCRIPT = r'''# Server Script - DocType Event: HD Ticket
# Event: Before Insert
# Purpose: Route new tickets with blank agent_group by HD Customer segment and shopplan.
# Safe-exec style: top-level only; helper functions cannot reliably see each other in DocType Event scripts.

SCRIPT_TITLE = "Profile - Ticket Routing"
MEDIUM_SCALE_TEAM = "Medium - Scale"
MEDIUM_GROW_TEAM = "Medium - Grow"
DEFAULT_TEAM = "CS 60p"

# Manual/API agent_group already set; routing skipped.
current_agent_group = str(doc.get("agent_group") or "").strip()
customer_name = str(doc.get("customer") or "").strip()

if not current_agent_group:
    customer_segment_value = ""
    shopplan_name = ""
    source = "default"

    if customer_name and frappe.db.exists("HD Customer", customer_name):
        customer_segment_value = str(frappe.db.get_value("HD Customer", customer_name, "custom_customer_segment") or "").strip()
        shopplan_name = str(frappe.db.get_value("HD Customer", customer_name, "custom_shopplan_name") or "").strip()
        source = "hd_customer"
    else:
        customer_segment_value = str(doc.get("custom_customer_segment") or "").strip()
        source = "ticket"

    segment_key = customer_segment_value.lower().replace(" ", "").replace("-", "").replace("_", "")
    shopplan_key = shopplan_name.lower()
    target_team = DEFAULT_TEAM
    ticket_segment = "SME"
    ticket_shopplan = "SME"

    if segment_key == "medium":
        ticket_segment = "Medium"
        if "scale" in shopplan_key:
            target_team = MEDIUM_SCALE_TEAM
            ticket_shopplan = "Medium Scale"
        elif "grow" in shopplan_key:
            target_team = MEDIUM_GROW_TEAM
            ticket_shopplan = "Medium Grow"

    reason_detail = "Customer Segment=" + (customer_segment_value or "-") + ", Shopplan=" + (shopplan_name or "-") + ", Source=" + source + "."
    routing_reason_prefix = "Auto-routed:"
    reason = routing_reason_prefix + " " + reason_detail + " Target team=" + target_team + "."

    if frappe.db.exists("HD Team", target_team):
        doc.agent_group = target_team
        doc.custom_customer_segment = ticket_segment
        doc.custom_shopplan = ticket_shopplan
        doc.custom_haravan_service_plan = shopplan_name
        doc.custom_haravan_profile_status = "Complete"
        doc.custom_haravan_profile_error = ""
        doc.custom_haravan_profile_checked_at = frappe.utils.now()
        doc.custom_haravan_routing_reason = reason
    else:
        doc.custom_haravan_routing_reason = "Routing skipped: target team " + target_team + " does not exist. " + reason
'''


ASSIGNMENT_SERVER_SCRIPT = r'''# Server Script - DocType Event: HD Ticket
# Event: After Insert
# Purpose: Assign auto-routed new tickets by round robin within HD Team.users.
# Safe-exec style: top-level only; helper functions cannot reliably see each other in DocType Event scripts.

SCRIPT_TITLE = "Profile - Ticket Round Robin Assignment"
ROUTED_TEAMS = ["Medium - Scale", "Medium - Grow", "CS 60p"]

agent_group = str(doc.get("agent_group") or "").strip()
routing_reason = str(doc.get("custom_haravan_routing_reason") or "").strip()

if agent_group in ROUTED_TEAMS and routing_reason.startswith("Auto-routed:"):
    existing_assignments = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": "HD Ticket",
            "reference_name": doc.name,
            "status": "Open",
        },
        fields=["name"],
        limit=1,
    )

    if not existing_assignments:
        if not frappe.db.exists("HD Team", agent_group):
            frappe.log_error("Target team does not exist: " + agent_group, SCRIPT_TITLE)
        else:
            team = frappe.get_doc("HD Team", agent_group)
            active_users = []
            for row in team.get("users") or []:
                user_id = str(row.get("user") or "").strip()
                if user_id and frappe.db.exists("User", user_id):
                    enabled = frappe.db.get_value("User", user_id, "enabled")
                    if enabled in (1, "1", True):
                        active_users.append(user_id)

            if not active_users:
                frappe.log_error("No active users in HD Team: " + agent_group, SCRIPT_TITLE)
            else:
                assignment_description = "Auto round-robin assignment for " + agent_group
                last_user = ""
                previous_assignments = frappe.get_all(
                    "ToDo",
                    filters={
                        "reference_type": "HD Ticket",
                        "description": assignment_description,
                    },
                    fields=["allocated_to"],
                    order_by="creation desc",
                    limit=1,
                )
                if previous_assignments:
                    last_user = str(previous_assignments[0].get("allocated_to") or "").strip()

                selected_user = active_users[0]
                if last_user:
                    for idx in range(len(active_users)):
                        if active_users[idx] == last_user:
                            selected_user = active_users[(idx + 1) % len(active_users)]
                            break

                assignment_error = ""
                try:
                    frappe.desk.form.assign_to.add(
                        {
                            "assign_to": [selected_user],
                            "doctype": "HD Ticket",
                            "name": doc.name,
                            "description": assignment_description,
                            "notify": 0,
                        }
                    )
                except Exception as exc:
                    assignment_error = str(exc)[:500]

                if assignment_error:
                    try:
                        todo = frappe.new_doc("ToDo")
                        todo.allocated_to = selected_user
                        todo.reference_type = "HD Ticket"
                        todo.reference_name = doc.name
                        todo.status = "Open"
                        todo.description = assignment_description
                        todo.flags.ignore_permissions = True
                        todo.insert(ignore_permissions=True)
                        assignment_error = ""
                    except Exception as exc:
                        assignment_error = assignment_error + "\nFallback ToDo insert failed: " + str(exc)[:500]

                if assignment_error:
                    frappe.log_error("Cannot assign ticket " + doc.name + " to " + selected_user + "\n" + assignment_error, SCRIPT_TITLE)
'''


SERVER_SCRIPT_SPECS = [
    {
        "name": SERVER_SCRIPT_NAME,
        "event": DOCTYPE_EVENT,
        "script": SERVER_SCRIPT,
        "backup_prefix": "routing",
        "compile_label": "profile-ticket-routing-server-script",
    },
    {
        "name": ASSIGNMENT_SERVER_SCRIPT_NAME,
        "event": ASSIGNMENT_DOCTYPE_EVENT,
        "script": ASSIGNMENT_SERVER_SCRIPT,
        "backup_prefix": "assignment",
        "compile_label": "profile-ticket-assignment-server-script",
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
    url = f"{site}/api/resource/{encoded_doctype}"
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


def _deploy_server_script(session: requests.Session, site: str, spec: dict) -> dict:
    payload = {
        "script_type": "DocType Event",
        "reference_doctype": REFERENCE_DOCTYPE,
        "doctype_event": spec["event"],
        "disabled": 0,
        "script": spec["script"],
    }
    return upsert_doc(session, site, "Server Script", spec["name"], payload)


def deploy_server_script(session: requests.Session, site: str) -> dict:
    return _deploy_server_script(session, site, SERVER_SCRIPT_SPECS[0])


def deploy_assignment_server_script(session: requests.Session, site: str) -> dict:
    return _deploy_server_script(session, site, SERVER_SCRIPT_SPECS[1])


def _write_backup(path: Path, doc: dict):
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    site = env("HARAVAN_HELP_SITE").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET")

    for spec in SERVER_SCRIPT_SPECS:
        compile(spec["script"], f"<{spec['compile_label']}>", "exec")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_key}:{api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    backup_dir = Path("backups") / f"profile_ticket_routing_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    deployed = []
    for spec in SERVER_SCRIPT_SPECS:
        existing = get_doc(session, site, "Server Script", spec["name"])
        action = "updated" if existing else "created"
        if existing:
            _write_backup(backup_dir / f"{spec['backup_prefix']}_server_script_before.json", existing)

        updated = _deploy_server_script(session, site, spec)
        _write_backup(backup_dir / f"{spec['backup_prefix']}_server_script_after.json", updated)
        deployed.append(
            {
                "name": spec["name"],
                "reference_doctype": REFERENCE_DOCTYPE,
                "doctype_event": spec["event"],
                "action": action,
            }
        )

    print(
        json.dumps(
            {
                "status": "success",
                "site": site,
                "deployed": deployed,
                "backup_dir": str(backup_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
