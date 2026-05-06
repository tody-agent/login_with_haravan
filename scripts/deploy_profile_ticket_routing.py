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
REFERENCE_DOCTYPE = "HD Ticket"
DOCTYPE_EVENT = "Before Save"


SERVER_SCRIPT = r'''# Server Script - DocType Event: HD Ticket
# Event: Before Save
# Purpose: Route tickets by HD Customer/Bitrix SME/Medium segment without adding a competing script.
# Safe-exec style: top-level only; helper functions cannot reliably see each other in DocType Event scripts.

SCRIPT_TITLE = "Profile - Ticket Routing"
SETTINGS_DOCTYPE = "Helpdesk Integrations Settings"
AUTO_ROUTED_AGENT_GROUPS = ["", "Medium", "CS 60p", "After Sales", "Service Ecom"]
MEDIUM_TEAM = "Medium"
SME_TEAM = "CS 60p"

org_id = str(doc.get("custom_orgid") or "").strip()
customer_name = str(doc.get("customer") or "").strip()
profile_org_id = str(doc.get("custom_haravan_profile_orgid") or "").strip()

ticket_segment_value = str(doc.get("custom_customer_segment") or "").strip()
ticket_segment_key = ticket_segment_value.lower().replace(" ", "").replace("-", "").replace("_", "")
ticket_segment = ""
if ticket_segment_key == "medium":
    ticket_segment = "Medium"
elif ticket_segment_key == "sme":
    ticket_segment = "SME"

segment = ""
source = ""
reason_detail = ""

if customer_name and frappe.db.exists("HD Customer", customer_name):
    hd_customer_segment_value = str(frappe.db.get_value("HD Customer", customer_name, "custom_customer_segment") or "").strip()
    hd_customer_segment_key = hd_customer_segment_value.lower().replace(" ", "").replace("-", "").replace("_", "")
    if hd_customer_segment_key == "medium":
        segment = "Medium"
        source = "hd_customer"
        reason_detail = "HD Customer.custom_customer_segment=Medium."
    elif hd_customer_segment_key == "sme":
        segment = "SME"
        source = "hd_customer"
        reason_detail = "HD Customer.custom_customer_segment=SME."

if not segment and org_id and ticket_segment and profile_org_id == org_id:
    segment = ticket_segment
    source = "ticket_cache"
    reason_detail = "Cached ticket segment for OrgID " + org_id + "."

if not segment:
    if not org_id:
        segment = "SME"
        source = "missing_orgid"
        reason_detail = "Ticket has no OrgID; defaulted to SME."
        if str(doc.get("custom_haravan_profile_status") or "").strip() != "Missing OrgID":
            doc.custom_haravan_profile_status = "Missing OrgID"
        doc.custom_haravan_profile_error = "Ticket has no OrgID yet; defaulted to SME routing."
    else:
        settings = None
        try:
            settings = frappe.get_doc(SETTINGS_DOCTYPE)
        except Exception:
            settings = None

        bitrix_enabled = True
        bitrix_webhook_url = ""
        if settings:
            try:
                bitrix_enabled = str(settings.get("bitrix_enabled") if settings.get("bitrix_enabled") is not None else "1").strip().lower() in ("1", "true", "yes", "on", "enabled")
            except Exception:
                bitrix_enabled = True
            try:
                bitrix_webhook_url = settings.get_password("bitrix_webhook_url") or ""
            except Exception:
                bitrix_webhook_url = ""
            if not bitrix_webhook_url:
                try:
                    bitrix_webhook_url = settings.get("bitrix_webhook_url") or ""
                except Exception:
                    bitrix_webhook_url = ""
        if not bitrix_webhook_url:
            try:
                bitrix_webhook_url = frappe.db.get_single_value(SETTINGS_DOCTYPE, "bitrix_webhook_url") or ""
            except Exception:
                bitrix_webhook_url = ""

        if not bitrix_enabled:
            segment = "SME"
            source = "bitrix_disabled"
            reason_detail = "Bitrix disabled; defaulted to SME."
            doc.custom_haravan_profile_status = "Skipped"
            doc.custom_haravan_profile_error = "Bitrix enrichment is disabled; defaulted to SME routing."
        elif not bitrix_webhook_url:
            segment = "SME"
            source = "bitrix_missing_config"
            reason_detail = "Bitrix webhook missing; defaulted to SME."
            doc.custom_haravan_profile_status = "Skipped"
            doc.custom_haravan_profile_error = "Bitrix webhook is missing; defaulted to SME routing."
        else:
            company_rows = []
            company_error = ""
            url = bitrix_webhook_url.rstrip("/") + "/crm.company.list.json"
            payload = {
                "FILTER": {"UF_CRM_COMPANY_ID": org_id},
                "SELECT": [
                    "ID",
                    "TITLE",
                    "UF_CRM_COMPANY_ID",
                    "UF_CRM_CURRENT_SHOPPLAN",
                    "UF_CRM_LAST_HSI_SEGMENT",
                    "UF_CRM_CURRENT_HSI_SEGMENT",
                ],
                "ORDER": {"DATE_MODIFY": "DESC"},
            }
            try:
                result = frappe.make_post_request(url, headers={"Content-Type": "application/json"}, json=payload)
                if isinstance(result, str):
                    result = frappe.parse_json(result)
                if isinstance(result, dict):
                    company_rows = result.get("result") or []
                if not isinstance(company_rows, list):
                    company_rows = []
            except Exception as exc:
                company_error = str(exc)[:500]
                frappe.log_error("Cannot fetch Bitrix company for OrgID " + org_id + "\n" + company_error, SCRIPT_TITLE)

            if company_rows:
                company = company_rows[0]
                current_shopplan = str(company.get("UF_CRM_CURRENT_SHOPPLAN") or "").strip()
                current_shopplan_key = current_shopplan.lower()
                last_hsi_segment = str(company.get("UF_CRM_LAST_HSI_SEGMENT") or "").strip()
                current_hsi_segment = str(company.get("UF_CRM_CURRENT_HSI_SEGMENT") or "").strip()

                if "grow" in current_shopplan_key or "scale" in current_shopplan_key:
                    segment = "Medium"
                elif last_hsi_segment == "HSI_500+":
                    segment = "Medium"
                else:
                    segment = "SME"
                source = "bitrix"
                reason_detail = "Bitrix profile: Current Shopplan=" + (current_shopplan or "-") + ", Last HSI Segment=" + (last_hsi_segment or "-") + "."
                doc.custom_haravan_profile_status = "Complete"
                doc.custom_haravan_profile_error = ""
                doc.custom_haravan_profile_orgid = org_id
                if current_shopplan:
                    doc.custom_haravan_service_plan = current_shopplan
                    if "grow" in current_shopplan_key:
                        doc.custom_shopplan = "Medium Grow"
                    elif "scale" in current_shopplan_key:
                        doc.custom_shopplan = "Medium Scale"
                    else:
                        doc.custom_shopplan = "SME"
                if current_hsi_segment:
                    doc.custom_haravan_hsi_segment = current_hsi_segment
            elif company_error:
                segment = "SME"
                source = "bitrix_error"
                reason_detail = "Bitrix error; defaulted to SME."
                doc.custom_haravan_profile_status = "API Error"
                doc.custom_haravan_profile_error = company_error
                doc.custom_haravan_profile_orgid = org_id
            else:
                segment = "SME"
                source = "bitrix_not_found"
                reason_detail = "No Bitrix company found for OrgID " + org_id + "; defaulted to SME."
                doc.custom_haravan_profile_status = "Complete"
                doc.custom_haravan_profile_error = "No Bitrix company found; defaulted to SME routing."
                doc.custom_haravan_profile_orgid = org_id

if segment:
    if str(doc.get("custom_customer_segment") or "").strip() != segment:
        doc.custom_customer_segment = segment
    if org_id and str(doc.get("custom_haravan_profile_orgid") or "").strip() != org_id:
        doc.custom_haravan_profile_orgid = org_id
    doc.custom_haravan_profile_checked_at = frappe.utils.now()

    if source != "hd_customer" and customer_name and frappe.db.exists("HD Customer", customer_name):
        try:
            current_customer_segment_value = str(frappe.db.get_value("HD Customer", customer_name, "custom_customer_segment") or "").strip()
            current_customer_segment_key = current_customer_segment_value.lower().replace(" ", "").replace("-", "").replace("_", "")
            current_customer_segment = ""
            if current_customer_segment_key == "medium":
                current_customer_segment = "Medium"
            elif current_customer_segment_key == "sme":
                current_customer_segment = "SME"
            if current_customer_segment != segment:
                frappe.db.set_value("HD Customer", customer_name, "custom_customer_segment", segment, update_modified=False)
        except Exception as exc:
            frappe.log_error("Cannot update HD Customer segment for " + customer_name + "\n" + str(exc)[:500], SCRIPT_TITLE)

    target_team = SME_TEAM
    if segment == "Medium":
        target_team = MEDIUM_TEAM

    reason = "Customer Segment " + segment + " routes to " + target_team + ". Source: " + source + ". " + reason_detail
    if not frappe.db.exists("HD Team", target_team):
        doc.custom_haravan_routing_reason = "Target team " + target_team + " does not exist. " + reason
    else:
        current_agent_group = str(doc.get("agent_group") or "").strip()
        if current_agent_group in AUTO_ROUTED_AGENT_GROUPS:
            doc.agent_group = target_team
        doc.custom_haravan_routing_reason = reason
'''


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


def deploy_server_script(session: requests.Session, site: str) -> dict:
    payload = {
        "script_type": "DocType Event",
        "reference_doctype": REFERENCE_DOCTYPE,
        "doctype_event": DOCTYPE_EVENT,
        "disabled": 0,
        "script": SERVER_SCRIPT,
    }
    return upsert_doc(session, site, "Server Script", SERVER_SCRIPT_NAME, payload)


def main() -> int:
    site = env("HARAVAN_HELP_SITE").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET")

    compile(SERVER_SCRIPT, "<profile-ticket-routing-server-script>", "exec")

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
    existing = get_doc(session, site, "Server Script", SERVER_SCRIPT_NAME)
    if existing:
        (backup_dir / "server_script_before.json").write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    updated = deploy_server_script(session, site)
    (backup_dir / "server_script_after.json").write_text(
        json.dumps(updated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Deployed Server Script: {SERVER_SCRIPT_NAME}")
    print(f"DocType event: {REFERENCE_DOCTYPE} / {DOCTYPE_EVENT}")
    print(f"Backup: {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
