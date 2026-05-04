#!/usr/bin/env python3
"""Deploy Bitrix metajson enrichment as Frappe Desk-managed Server Script.

This intentionally does not add runtime code to the custom app. It creates the
small Custom Fields needed for loop/resource guards, then upserts an API Server
Script that metajson workflows can call by Haravan orgid.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


SERVER_SCRIPT_NAME = "Metajson - Bitrix Company Enrichment API"
API_METHOD = "haravan_bitrix_metajson_company_enrichment"

CUSTOM_FIELDS = [
    {
        "dt": "HD Customer",
        "fieldname": "custom_bitrix_last_checked_at",
        "label": "Bitrix Last Checked At",
        "fieldtype": "Datetime",
        "insert_after": "custom_bitrix_last_synced_at",
        "read_only": 1,
    },
    {
        "dt": "HD Customer",
        "fieldname": "custom_bitrix_company_modified_at",
        "label": "Bitrix Company Modified At",
        "fieldtype": "Datetime",
        "insert_after": "custom_bitrix_last_checked_at",
        "read_only": 1,
    },
    {
        "dt": "HD Customer",
        "fieldname": "custom_bitrix_not_found_at",
        "label": "Bitrix Not Found At",
        "fieldtype": "Datetime",
        "insert_after": "custom_bitrix_company_modified_at",
        "read_only": 1,
    },
]


SERVER_SCRIPT = r'''# Server Script — API Method: haravan_bitrix_metajson_company_enrichment
# Purpose: On metajson orgid lookup, enrich HD Customer from Bitrix company data.
# Safe-exec style: keep logic top-level to avoid helper lookup issues.

orgid = frappe.form_dict.get("orgid") or frappe.form_dict.get("org_id") or frappe.form_dict.get("haravan_orgid")
if orgid is None:
    orgid = ""
orgid = str(orgid).strip()

force_raw = str(frappe.form_dict.get("force") or "").strip().lower()
force = force_raw in ("1", "true", "yes", "on")
ticket_name = frappe.form_dict.get("ticket") or frappe.form_dict.get("ticket_name") or frappe.form_dict.get("hd_ticket")
ticket_name = str(ticket_name or "").strip()

message = {"success": True, "data": {"status": "missing_orgid"}, "message": "No orgid supplied."}

if orgid:
    settings = None
    if frappe.db.exists("DocType", "Helpdesk Integrations Settings"):
        try:
            settings = frappe.get_doc("Helpdesk Integrations Settings")
        except Exception:
            settings = None

    enabled = True
    webhook_url = None
    portal_url = None
    timeout_seconds = 15
    ttl_minutes = 60

    if settings:
        try:
            enabled = bool(int(settings.get("bitrix_enabled") if settings.get("bitrix_enabled") is not None else 1))
        except Exception:
            enabled = bool(settings.get("bitrix_enabled"))
        try:
            webhook_url = settings.get_password("bitrix_webhook_url")
        except Exception:
            webhook_url = None
        if not webhook_url:
            webhook_url = settings.get("bitrix_webhook_url")
        portal_url = settings.get("bitrix_portal_url")
        try:
            timeout_seconds = int(settings.get("bitrix_timeout_seconds") or 15)
        except Exception:
            timeout_seconds = 15
        try:
            ttl_minutes = int(settings.get("bitrix_refresh_ttl_minutes") or 60)
        except Exception:
            ttl_minutes = 60

    if not enabled:
        message = {"success": True, "data": {"status": "disabled"}, "message": "Bitrix enrichment is disabled."}
    elif not webhook_url:
        message = {"success": True, "data": {"status": "missing_config"}, "message": "Bitrix webhook is not configured."}
    else:
        orgid_int = None
        try:
            orgid_int = int(orgid)
        except Exception:
            orgid_int = None

        ticket_current_customer = None
        if ticket_name and frappe.db.exists("HD Ticket", ticket_name):
            ticket_current_customer = frappe.db.get_value("HD Ticket", ticket_name, "customer")
        customer_name = frappe.form_dict.get("hd_customer") or ticket_current_customer
        if not customer_name and orgid_int is not None:
            lookup_value = orgid_int if orgid_int is not None else orgid
            customer_name = frappe.db.get_value("HD Customer", {"custom_haravan_orgid": lookup_value}, "name", cache=False)

        now_value = frappe.utils.now_datetime()
        customer = frappe.get_doc("HD Customer", customer_name) if customer_name else None
        customer_meta = frappe.get_meta("HD Customer")
        has_last_checked = customer_meta.has_field("custom_bitrix_last_checked_at")
        has_not_found = customer_meta.has_field("custom_bitrix_not_found_at")
        has_company_id = customer_meta.has_field("custom_bitrix_company_id")
        has_company_url = customer_meta.has_field("custom_bitrix_company_url")
        has_confidence = customer_meta.has_field("custom_bitrix_match_confidence")
        has_status = customer_meta.has_field("custom_bitrix_sync_status")
        has_last_synced = customer_meta.has_field("custom_bitrix_last_synced_at")
        has_myharavan = customer_meta.has_field("custom_myharavan")
        has_company_modified = customer_meta.has_field("custom_bitrix_company_modified_at")

        if customer and has_last_checked and not force:
            last_checked = customer.get("custom_bitrix_last_checked_at")
            if last_checked:
                try:
                    age_seconds = frappe.utils.time_diff_in_seconds(now_value, last_checked)
                except Exception:
                    age_seconds = ttl_minutes * 60 + 1
                if age_seconds < ttl_minutes * 60:
                    message = {
                        "success": True,
                        "data": {"status": "cached", "hd_customer": customer.name},
                        "message": "Bitrix check skipped by TTL.",
                    }
                    frappe.response["message"] = message

        if frappe.response.get("message") is None:
                webhook_base = webhook_url.rstrip("/") + "/"
                company_result = []
                lookup_field = "UF_CRM_HARAVAN_ORG_ID"
                for fieldname in ("UF_CRM_HARAVAN_ORG_ID", "UF_CRM_COMPANY_ID"):
                    payload = {
                        "filter": {fieldname: orgid},
                        "select": ["*", "UF_*", "EMAIL", "PHONE", "WEB"],
                        "order": {"DATE_MODIFY": "DESC"},
                    }
                    try:
                        result = frappe.make_post_request(
                            webhook_base + "crm.company.list.json",
                            data=json.dumps(payload),
                            headers={"Content-Type": "application/json"},
                        )
                    except Exception as exc:
                        frappe.log_error("Bitrix metajson company fetch failed: " + str(exc)[:800], "Bitrix metajson company fetch failed")
                        message = {"success": False, "data": {"status": "error"}, "message": "Bitrix company fetch failed."}
                        result = None
                        break
                    company_result = result.get("result") or [] if isinstance(result, dict) else []
                    lookup_field = fieldname
                    if company_result:
                        break

                if message.get("data", {}).get("status") != "error":
                    company = company_result[0] if company_result else None
                    if not company:
                        if customer and has_last_checked:
                            frappe.db.set_value("HD Customer", customer.name, "custom_bitrix_last_checked_at", now_value, update_modified=False)
                        if customer and has_not_found:
                            frappe.db.set_value("HD Customer", customer.name, "custom_bitrix_not_found_at", now_value, update_modified=False)
                        message = {
                            "success": True,
                            "data": {"status": "not_found", "hd_customer": customer.name if customer else None},
                            "message": "No Bitrix company found.",
                        }
                    else:
                        company_id = str(company.get("ID") or company.get("id") or "")
                        company_title = company.get("TITLE") or company.get("NAME") or orgid
                        company_modified = company.get("DATE_MODIFY") or company.get("DATE_MODIFIED") or company.get("MODIFY_DATE")
                        if not customer and has_company_id and company_id:
                            existing_customer = frappe.db.get_value("HD Customer", {"custom_bitrix_company_id": company_id}, "name", cache=False)
                            if existing_customer:
                                customer = frappe.get_doc("HD Customer", existing_customer)

                        if not portal_url and "/rest/" in webhook_url:
                            portal_url = webhook_url.split("/rest/")[0]
                        company_url = (portal_url.rstrip("/") + "/crm/company/details/" + company_id + "/") if portal_url and company_id else None

                        if not customer:
                            customer = frappe.new_doc("HD Customer")
                            customer.customer_name = str(company_title) + " - " + orgid
                            customer.domain = orgid if "." in orgid else orgid + ".myharavan.com"
                            if orgid_int is not None:
                                customer.custom_haravan_orgid = orgid_int
                            if has_myharavan:
                                customer.custom_myharavan = orgid if "." in orgid else orgid + ".myharavan.com"
                            customer.flags.ignore_permissions = True
                            customer.insert(ignore_permissions=True)

                        if True:
                            changed = False
                            if has_company_id and company_id and str(customer.get("custom_bitrix_company_id") or "") != company_id:
                                customer.set("custom_bitrix_company_id", company_id)
                                changed = True
                            if has_company_url and company_url and str(customer.get("custom_bitrix_company_url") or "") != company_url:
                                customer.set("custom_bitrix_company_url", company_url)
                                changed = True
                            if has_confidence and customer.get("custom_bitrix_match_confidence") != 95:
                                customer.set("custom_bitrix_match_confidence", 95)
                                changed = True
                            if has_status and customer.get("custom_bitrix_sync_status") != "matched":
                                customer.set("custom_bitrix_sync_status", "matched")
                                changed = True
                            if has_last_synced:
                                customer.set("custom_bitrix_last_synced_at", now_value)
                                changed = True
                            if has_last_checked:
                                customer.set("custom_bitrix_last_checked_at", now_value)
                                changed = True
                            if has_company_modified and company_modified:
                                customer.set("custom_bitrix_company_modified_at", company_modified)
                                changed = True
                            if changed:
                                customer.flags.ignore_permissions = True
                                customer.save(ignore_permissions=True)

                            if frappe.db.exists("DocType", "HD Customer Data") and company_id:
                                filters = {
                                    "hd_customer": customer.name,
                                    "source": "bitrix",
                                    "entity_type": "company",
                                    "external_id": company_id,
                                }
                                existing_data = frappe.db.exists("HD Customer Data", filters)
                                data_doc = frappe.get_doc("HD Customer Data", existing_data) if existing_data else frappe.new_doc("HD Customer Data")
                                data_doc.update(filters)
                                data_doc.contact = None
                                data_doc.external_url = company_url
                                data_doc.match_key = "haravan_orgid:" + lookup_field
                                data_doc.confidence = 95
                                data_doc.last_synced_at = now_value
                                data_doc.summary_json = json.dumps(company, ensure_ascii=False, sort_keys=True, default=str)
                                data_doc.flags.ignore_permissions = True
                                if existing_data:
                                    data_doc.save(ignore_permissions=True)
                                else:
                                    data_doc.insert(ignore_permissions=True)
                            ticket_linked = False
                            ticket_previous_customer = None
                            if ticket_name and frappe.db.exists("HD Ticket", ticket_name):
                                ticket_previous_customer = frappe.db.get_value("HD Ticket", ticket_name, "customer")
                                if ticket_previous_customer != customer.name:
                                    frappe.db.set_value("HD Ticket", ticket_name, "customer", customer.name)
                                ticket_linked = True

                            message = {
                                "success": True,
                                "data": {
                                    "status": "matched",
                                    "hd_customer": customer.name,
                                    "ticket": {
                                        "name": ticket_name,
                                        "linked": ticket_linked,
                                        "previous_customer": ticket_previous_customer,
                                    },
                                    "company": {"id": company_id, "title": company_title, "date_modify": company_modified},
                                },
                                "message": "Bitrix company data synced.",
                            }

frappe.response["message"] = message
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


def ensure_custom_fields(session: requests.Session, site: str) -> list[str]:
    changed: list[str] = []
    for field in CUSTOM_FIELDS:
        name = f"{field['dt']}-{field['fieldname']}"
        if get_doc(session, site, "Custom Field", name):
            continue
        payload = dict(field)
        payload["name"] = name
        upsert_doc(session, site, "Custom Field", name, payload)
        changed.append(name)
    return changed


def deploy_server_script(session: requests.Session, site: str) -> dict:
    payload = {
        "script_type": "API",
        "api_method": API_METHOD,
        "allow_guest": 0,
        "disabled": 0,
        "script": SERVER_SCRIPT,
    }
    return upsert_doc(session, site, "Server Script", SERVER_SCRIPT_NAME, payload)


def main() -> int:
    site = env("HARAVAN_HELP_SITE").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET")

    compile(SERVER_SCRIPT, "<bitrix-metajson-server-script>", "exec")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_key}:{api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    backup_dir = Path("backups") / f"bitrix_metajson_enrichment_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    existing = get_doc(session, site, "Server Script", SERVER_SCRIPT_NAME)
    if existing:
        (backup_dir / "server_script_before.json").write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    changed_fields = ensure_custom_fields(session, site)
    updated = deploy_server_script(session, site)
    (backup_dir / "server_script_after.json").write_text(
        json.dumps(updated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Deployed Server Script: {SERVER_SCRIPT_NAME}")
    print(f"API method: {API_METHOD}")
    print(f"Custom fields created: {', '.join(changed_fields) if changed_fields else 'none'}")
    print(f"Backup: {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
