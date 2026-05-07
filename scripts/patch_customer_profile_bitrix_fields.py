#!/usr/bin/env python3
"""Patch live Customer Profile Bitrix API and form UI with expanded company fields."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


FORM_SCRIPT_NAME = "Profile - Ticket Customer Button"
SERVER_SCRIPT_NAME = "Profile - Bitrix Customer API"
ENV_PATHS = ("/Volumes/Data/Skills/frappe_helpdesk/.env",)


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


def replace_once(source: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if new in source:
        return source, False
    if old not in source:
        raise SystemExit(f"Could not find expected snippet while patching {label}.")
    return source.replace(old, new, 1), True


def replace_once_if_found(source: str, old: str, new: str) -> tuple[str, bool]:
    if new in source or old not in source:
        return source, False
    return source.replace(old, new, 1), True


def patch_server_script(source: str) -> tuple[str, bool]:
    changed = False

    field_old = '    "UF_CRM_HARAVAN_MEMBERSHIP": "membership",\n    "ASSIGNED_BY_ID": "assigned_by_id",'
    field_new = '''    "UF_CRM_HARAVAN_MEMBERSHIP": "membership",
    "UF_CRM_1778130421650": "customer_segment",
    "ADDRESS_REGION": "address_region",
    "ADDRESS_COUNTRY": "address_country",
    "UF_CRM_VERIFIED_STATUS": "verified_status",
    "UF_CRM_COMPANY_STAGE": "company_stage",
    "UF_CRM_ID_FRESHSALES": "freshsales_id",
    "ASSIGNED_BY_ID": "assigned_by_id",'''
    source, did = replace_once(source, field_old, field_new, "server field map")
    changed = changed or did

    map_old = 'DECIMAL_KEYS = ["current_hsi_detail", "last_hsi_detail"]\n'
    map_new = '''DECIMAL_KEYS = ["current_hsi_detail", "last_hsi_detail"]
CUSTOMER_SEGMENT_MAP = {
    "15090": "SME",
    "15092": "Medium",
    "15094": "Enterprise",
}
'''
    source, did = replace_once(source, map_old, map_new, "server segment map")
    changed = changed or did

    normalize_old = '    result["company_name"] = strv(result.get("company_name")) or clean_title(result.get("title_full"), company_id)\n    result["url"] = public_url(cfg, "company", bitrix_id)\n'
    normalize_new = '''    result["company_name"] = strv(result.get("company_name")) or clean_title(result.get("title_full"), company_id)
    segment_code = strv(result.get("customer_segment"))
    if segment_code:
        result["customer_segment_code"] = segment_code
        result["customer_segment"] = CUSTOMER_SEGMENT_MAP.get(segment_code, segment_code)
    result["date_create"] = format_date(row.get("DATE_CREATE")) or strv(row.get("DATE_CREATE"))
    result["date_modify"] = format_date(row.get("DATE_MODIFY")) or strv(row.get("DATE_MODIFY"))
    result["url"] = public_url(cfg, "company", bitrix_id)
'''
    source, did = replace_once(source, normalize_old, normalize_new, "server normalize company")
    changed = changed or did

    customer_fields_old = 'customer_fields = ["name", "customer_name", "domain", "custom_haravan_orgid", "custom_haravan_company_id", "custom_myharavan", "custom_bitrix_company_id", "custom_bitrix_company_url", "custom_bitrix_match_confidence", "custom_bitrix_sync_status", "custom_bitrix_last_synced_at"]'
    customer_fields_new = 'customer_fields = ["name", "customer_name", "domain", "custom_haravan_orgid", "custom_haravan_company_id", "custom_myharavan", "custom_customer_segment", "custom_first_paid_date", "custom_shopplan_name", "custom_expired_date", "custom_hsi_segment", "custom_haravan_hsi_segment", "custom_bitrix_company_id", "custom_bitrix_company_url", "custom_bitrix_match_confidence", "custom_bitrix_sync_status", "custom_bitrix_last_synced_at"]'
    source, did = replace_once(source, customer_fields_old, customer_fields_new, "server customer fields")
    changed = changed or did

    save_old = '                    set_customer_values(customer_name, {"custom_bitrix_company_id": bitrix_id, "custom_bitrix_company_url": normalized_company.get("url"), "custom_bitrix_match_confidence": company_match.get("confidence"), "custom_bitrix_sync_status": "matched", "custom_bitrix_last_synced_at": now})\n'
    save_new = '''                    customer_updates = {"custom_bitrix_company_id": bitrix_id, "custom_bitrix_company_url": normalized_company.get("url"), "custom_bitrix_match_confidence": company_match.get("confidence"), "custom_bitrix_sync_status": "matched", "custom_bitrix_last_synced_at": now}
                    try:
                        customer_meta = frappe.get_meta("HD Customer")
                        optional_customer_updates = {
                            "custom_customer_segment": normalized_company.get("customer_segment"),
                            "custom_first_paid_date": normalized_company.get("first_shopplan_date"),
                            "custom_shopplan_name": normalized_company.get("current_shopplan"),
                            "custom_expired_date": normalized_company.get("shopplan_expiry"),
                            "custom_hsi_segment": normalized_company.get("current_hsi_segment"),
                            "custom_haravan_hsi_segment": normalized_company.get("current_hsi_segment"),
                        }
                        for fieldname, fieldvalue in optional_customer_updates.items():
                            if fieldvalue not in (None, "") and customer_meta.has_field(fieldname):
                                customer_updates[fieldname] = fieldvalue
                    except Exception:
                        pass
                    set_customer_values(customer_name, customer_updates)
'''
    source, did = replace_once(source, save_old, save_new, "server customer save")
    changed = changed or did

    return source, changed


def replace_block(source: str, start_marker: str, end_marker: str, replacement: str, label: str) -> tuple[str, bool]:
    if replacement in source:
        return source, False
    start = source.find(start_marker)
    if start == -1:
        raise SystemExit(f"Could not find start marker while patching {label}.")
    end = source.find(end_marker, start)
    if end == -1:
        raise SystemExit(f"Could not find end marker while patching {label}.")
    return source[:start] + replacement + source[end + len(end_marker) :], True


def replace_block_if_found(
    source: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    keep_end_marker: bool = True,
) -> tuple[str, bool]:
    if replacement in source:
        return source, False
    start = source.find(start_marker)
    if start == -1:
        return source, False
    end = source.find(end_marker, start)
    if end == -1:
        return source, False
    tail = source[end:] if keep_end_marker else source[end + len(end_marker) :]
    return source[:start] + replacement + tail, True


def patch_form_script(source: str) -> tuple[str, bool]:
    changed = False

    label_replacements = {
        "Mo Bitrix": "Mở",
        "Lam moi Bitrix": "Làm mới",
        "Dong bo": "Sao lưu",
        "Lam moi Freshdesk": "Làm mới",
        "Lam moi": "Làm mới",
    }
    for old, new in label_replacements.items():
        if old in source:
            source = source.replace(old, new)
            changed = True

    repaired = source.replace(
        "    const bitrixContactRows = [\n    const bitrixContactRows = [\n",
        "    const bitrixContactRows = [\n",
    )
    if repaired != source:
        source = repaired
        changed = True

    bitrix_rows = '''    const raw = company.raw_summary || company.summary || {};
    const bitrixRows = [
      ["Status", status],
      ["Bitrix ID", company.bitrix_id || company.id || raw.ID || bitrixId || customer.custom_bitrix_company_id],
      ["Title", company.title_full || company.title || company.company_name || raw.TITLE],
      ["Company", company.company_name || company.title || raw.COMPANY_TITLE || raw.TITLE],
      ["DATE_CREATE", company.date_create || raw.DATE_CREATE],
      ["DATE_MODIFY", company.date_modify || raw.DATE_MODIFY],
      ["ASSIGNED_BY_ID", company.assigned_by_id || raw.ASSIGNED_BY_ID],
      ["ADDRESS_REGION", company.address_region || raw.ADDRESS_REGION],
      ["ADDRESS_COUNTRY", company.address_country || raw.ADDRESS_COUNTRY],
      ["UF_CRM_VERIFIED_STATUS", company.verified_status || raw.UF_CRM_VERIFIED_STATUS],
      ["UF_CRM_COMPANY_STAGE", company.company_stage || raw.UF_CRM_COMPANY_STAGE],
      ["UF_CRM_ID_FRESHSALES", company.freshsales_id || raw.UF_CRM_ID_FRESHSALES],
      ["UF_CRM_COMPANY_ID", company.company_id || raw.UF_CRM_COMPANY_ID || companyId],
    ];

    const bitrixPlanRows = [
      ["HD Customer Segment", company.customer_segment || customer.custom_customer_segment],
      ["UF_CRM_1778130421650", company.customer_segment_code || raw.UF_CRM_1778130421650],
      ["UF_CRM_DATE_CREATED_SHOP", company.shop_created_date || raw.UF_CRM_DATE_CREATED_SHOP],
      ["UF_CRM_FIRST_PAID_DATE", company.first_shopplan_date || company.first_paid_date || raw.UF_CRM_FIRST_PAID_DATE],
      ["UF_CRM_CURRENT_SHOPPLAN", company.current_shopplan || company.shopplan || raw.UF_CRM_CURRENT_SHOPPLAN],
      ["UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN", company.current_shopplan_date || raw.UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN],
      ["UF_CRM_DATE_EXPIRED_SHOPPLAN", company.shopplan_expiry || company.expiry || company.expired_at || raw.UF_CRM_DATE_EXPIRED_SHOPPLAN],
      ["UF_CRM_CURRENT_HSI_SEGMENT", company.current_hsi_segment || company.hsi_segment || raw.UF_CRM_CURRENT_HSI_SEGMENT],
      ["UF_CRM_CURRENT_HSI_DETAIL", company.current_hsi_detail || raw.UF_CRM_CURRENT_HSI_DETAIL],
      ["UF_CRM_HARAVAN_MEMBERSHIP", company.membership || raw.UF_CRM_HARAVAN_MEMBERSHIP],
      ["Shopplan Status", company.shopplan_status],
      ["Days Left", company.shopplan_days_left],
    ];

    const bitrixOwnerRows = [
      ["UF_CRM_SHOP_OWNER_NAME", company.owner_name || raw.UF_CRM_SHOP_OWNER_NAME],
      ["UF_CRM_SHOP_OWNER_EMAIL", company.owner_email || raw.UF_CRM_SHOP_OWNER_EMAIL],
      ["UF_CRM_SHOP_OWNER_PHONE_NUMBER", company.owner_phone || raw.UF_CRM_SHOP_OWNER_PHONE_NUMBER],
      ["Assigned Name", responsible.name || company.assigned_by_name || company.assigned_name],
      ["Assigned Email", responsible.email || company.assigned_by_email],
      ["Responsible Status", responsible.status],
    ];

'''
    source, did = replace_block_if_found(
        source,
        "    const bitrixRows = [\n",
        "    const bitrixContactRows = [\n",
        bitrix_rows + "    const bitrixContactRows = [\n",
        keep_end_marker=False,
    )
    changed = changed or did

    old_layout_rows = '''  const raw = company.raw_summary || company.summary || {};
  const bitrixRows = [
    ["Status", status],
    ["Bitrix ID", company.bitrix_id || company.id || raw.ID || bitrixId || customer.custom_bitrix_company_id],
    ["Title", company.title_full || company.title || company.company_name || raw.TITLE],
    ["Company", company.company_name || company.title || raw.COMPANY_TITLE || raw.TITLE],
    ["DATE_CREATE", company.date_create || raw.DATE_CREATE],
    ["DATE_MODIFY", company.date_modify || raw.DATE_MODIFY],
    ["ASSIGNED_BY_ID", company.assigned_by_id || raw.ASSIGNED_BY_ID],
    ["ADDRESS_REGION", company.address_region || raw.ADDRESS_REGION],
    ["ADDRESS_COUNTRY", company.address_country || raw.ADDRESS_COUNTRY],
    ["UF_CRM_VERIFIED_STATUS", company.verified_status || raw.UF_CRM_VERIFIED_STATUS],
    ["UF_CRM_COMPANY_STAGE", company.company_stage || raw.UF_CRM_COMPANY_STAGE],
    ["UF_CRM_ID_FRESHSALES", company.freshsales_id || raw.UF_CRM_ID_FRESHSALES],
    ["UF_CRM_COMPANY_ID", company.company_id || raw.UF_CRM_COMPANY_ID || companyId],
  ];

  const bitrixPlanRows = [
    ["HD Customer Segment", company.customer_segment || customer.custom_customer_segment],
    ["UF_CRM_1778130421650", company.customer_segment_code || raw.UF_CRM_1778130421650],
    ["UF_CRM_DATE_CREATED_SHOP", company.shop_created_date || raw.UF_CRM_DATE_CREATED_SHOP],
    ["UF_CRM_FIRST_PAID_DATE", company.first_shopplan_date || company.first_paid_date || raw.UF_CRM_FIRST_PAID_DATE],
    ["UF_CRM_CURRENT_SHOPPLAN", company.current_shopplan || company.shopplan || raw.UF_CRM_CURRENT_SHOPPLAN],
    ["UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN", company.current_shopplan_date || raw.UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN],
    ["UF_CRM_DATE_EXPIRED_SHOPPLAN", company.shopplan_expiry || company.expiry || company.expired_at || raw.UF_CRM_DATE_EXPIRED_SHOPPLAN],
    ["UF_CRM_CURRENT_HSI_SEGMENT", company.current_hsi_segment || company.hsi_segment || raw.UF_CRM_CURRENT_HSI_SEGMENT],
    ["UF_CRM_CURRENT_HSI_DETAIL", company.current_hsi_detail || raw.UF_CRM_CURRENT_HSI_DETAIL],
    ["UF_CRM_HARAVAN_MEMBERSHIP", company.membership || raw.UF_CRM_HARAVAN_MEMBERSHIP],
    ["Shopplan Status", company.shopplan_status],
    ["Days Left", company.shopplan_days_left],
  ];

  const bitrixOwnerRows = [
    ["UF_CRM_SHOP_OWNER_NAME", company.owner_name || raw.UF_CRM_SHOP_OWNER_NAME],
    ["UF_CRM_SHOP_OWNER_EMAIL", company.owner_email || raw.UF_CRM_SHOP_OWNER_EMAIL],
    ["UF_CRM_SHOP_OWNER_PHONE_NUMBER", company.owner_phone || raw.UF_CRM_SHOP_OWNER_PHONE_NUMBER],
    ["Assigned Name", responsible.name || company.assigned_by_name || company.assigned_name],
    ["Assigned Email", responsible.email || company.assigned_by_email],
    ["Responsible Status", responsible.status],
  ];

  const bitrixContactRows = [
    ["Contact", bitrixContact.title || bitrixContact.name],
    ["Contact ID", bitrixContact.contact_id || bitrixContact.ID || bitrixContact.id || contact.custom_bitrix_contact_id],
    ["Contact URL", bitrixContact.url || contact.custom_bitrix_contact_url],
  ];

  const ticketRows = [
    ["Ticket", ticket.name || doc.name],
    ["Raised By", ticket.raised_by || doc.raised_by],
    ["Contact", contact.full_name || contact.name || doc.contact],
    ["Email", contact.email_id || doc.raised_by],
    ["Phone", contact.mobile_no || contact.phone || doc.custom_contact_phone],
    ["Store URL", doc.custom_store_url],
    ["MyHaravan", doc.custom_myharavan_domain || doc.custom_my_haravan_domain],
    ["Org ID", ticket.custom_orgid || doc.custom_orgid || doc.custom_haravan_profile_orgid],
    ["Service Group", doc.custom_service_group || doc.agent_group],
    ["Service Name", doc.custom_service_name],
  ];

'''
    source, did = replace_block_if_found(
        source,
        "  const bitrixRows = [\n",
        "\n  const row = ([label, value]) => {",
        old_layout_rows,
    )
    changed = changed or did

    bitrix_section_new = '''      ${sectionHtml("Bitrix", bitrixRows)}
      ${sectionHtml("Shopplan & Segment", bitrixPlanRows)}
      ${sectionHtml("Shop Owner", bitrixOwnerRows)}
      ${sectionHtml("Bitrix Contact", bitrixContactRows)}'''
    bitrix_section_old = '      ${sectionHtml("Bitrix", bitrixRows)}\n      ${sectionHtml("Bitrix Contact", bitrixContactRows)}'
    source, did = replace_once_if_found(source, bitrix_section_old, bitrix_section_new)
    changed = changed or did

    old_bitrix_table = '''    <h3>Bitrix</h3>
    <div class="hcp-table">${bitrixRows.map(row).join("")}</div>'''
    new_bitrix_table = '''    <h3>Bitrix</h3>
    <div class="hcp-table">${bitrixRows.map(row).join("")}</div>
    <h3>Shopplan & Segment</h3>
    <div class="hcp-table">${bitrixPlanRows.map(row).join("")}</div>
    <h3>Shop Owner</h3>
    <div class="hcp-table">${bitrixOwnerRows.map(row).join("")}</div>
    <h3>Bitrix Contact</h3>
    <div class="hcp-table">${bitrixContactRows.map(row).join("")}</div>
    <h3>Thong tin ticket</h3>
    <div class="hcp-table">${ticketRows.map(row).join("")}</div>'''
    if old_bitrix_table in source and "Shopplan & Segment" not in source[source.find(old_bitrix_table) : source.find(old_bitrix_table) + 500]:
        source = source.replace(old_bitrix_table, new_bitrix_table, 1)
        changed = True

    stats_old = '          ${stat("Segment", customer.custom_customer_segment)}\n          ${stat("Shopplan", customer.custom_shopplan_name)}'
    stats_new = '          ${stat("Segment", customer.custom_customer_segment || company.customer_segment)}\n          ${stat("Shopplan", customer.custom_shopplan_name || company.current_shopplan)}'
    source, did = replace_once_if_found(source, stats_old, stats_new)
    changed = changed or did

    bitrix_stats_old = '        ${stat("Assigned", responsible.email || responsible.name || company.assigned_name)}'
    bitrix_stats_new = '        ${stat("Segment", company.customer_segment || customer.custom_customer_segment)}\n        ${stat("Shopplan", company.current_shopplan || company.shopplan || customer.custom_shopplan_name)}'
    source, did = replace_once_if_found(source, bitrix_stats_old, bitrix_stats_new)
    changed = changed or did

    source, did = replace_once_if_found(
        source,
        '${esc(company.company_name || company.title || title)}',
        '${esc(company.company_name || company.title_full || company.title || raw.TITLE || title)}',
    )
    changed = changed or did

    source, did = replace_once_if_found(
        source,
        '${escapeHtml(company.company_name || company.title || title)}',
        '${escapeHtml(company.company_name || company.title_full || company.title || raw.TITLE || title)}',
    )
    changed = changed or did

    source, did = replace_once_if_found(
        source,
        '${stat("Bitrix ID", company.bitrix_id || company.id || bitrixId)}',
        '${stat("Bitrix ID", company.bitrix_id || company.id || raw.ID || bitrixId || customer.custom_bitrix_company_id)}',
    )
    changed = changed or did

    source, did = replace_once_if_found(
        source,
        '${stat("Bitrix ID", company.bitrix_id || company.id || customer.bitrix_company_id)}',
        '${stat("Bitrix ID", company.bitrix_id || company.id || raw.ID || bitrixId || customer.custom_bitrix_company_id)}',
    )
    changed = changed or did

    return source, changed


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

    backup_dir = Path("backups") / f"customer_profile_bitrix_fields_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    targets = [
        ("Server Script", SERVER_SCRIPT_NAME, patch_server_script),
        ("HD Form Script", FORM_SCRIPT_NAME, patch_form_script),
    ]
    changed: list[str] = []

    for doctype, name, patcher in targets:
        url = resource_url(site, doctype, name)
        current = request_json(session, "GET", url)["data"]
        before_path = backup_dir / f"{doctype.replace(' ', '_')}_{name.replace(' ', '_')}_before.json"
        before_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

        patched_script, did_change = patcher(current.get("script") or "")
        if did_change:
            current = request_json(session, "PUT", url, data=json.dumps({"script": patched_script}))["data"]
            changed.append(name)

        after_path = backup_dir / f"{doctype.replace(' ', '_')}_{name.replace(' ', '_')}_after.json"
        after_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"changed": changed, "backup_dir": str(backup_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
