"""On-demand Helpdesk customer profile enrichment from Bitrix."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from login_with_haravan.engines.bitrix_api import BitrixClient
from login_with_haravan.engines.site_config import get_bitrix_config


def get_ticket_customer_profile(ticket: str | int, refresh: bool = False) -> dict[str, Any]:
    context = _ticket_context(ticket)
    if not context:
        return {"success": False, "data": {}, "message": "Ticket not found."}

    hd_customer = context.get("customer")
    contact = context.get("contact")

    if hd_customer and refresh:
        return refresh_customer_profile(hd_customer, contact, refresh=refresh, ticket=str(ticket))

    if hd_customer:
        customer_doc = frappe.get_doc("HD Customer", hd_customer)
        contact_doc = frappe.get_doc("Contact", contact) if contact else None
        return _profile_response(
            customer_doc,
            contact_doc,
            _stored_bitrix_summary(customer_doc, contact_doc),
            "Customer profile loaded.",
            ticket=context,
        )

    return _ticket_only_response(context, "Ticket has no linked HD Customer.")


def get_ticket_bitrix_profile(ticket: str | int, refresh: bool = True) -> dict[str, Any]:
    context = _ticket_context(ticket)
    if not context:
        return {"success": False, "data": {}, "message": "Ticket not found."}

    hd_customer = context.get("customer")
    contact = context.get("contact")
    if hd_customer:
        return refresh_customer_profile(hd_customer, contact, refresh=refresh, ticket=str(ticket))

    contact_doc = frappe.get_doc("Contact", contact) if contact else None
    config = get_bitrix_config()
    bitrix_data: dict[str, Any] = {
        "enabled": bool(config.get("enabled")),
        "configured": bool(config.get("configured")),
        "company": None,
        "contact": None,
        "responsible": None,
        "status": "disabled",
    }

    if not config.get("enabled"):
        return _ticket_only_response(context, "Bitrix enrichment is disabled.", contact_doc, bitrix_data)
    if not config.get("configured"):
        bitrix_data["status"] = "missing_config"
        return _ticket_only_response(context, "Bitrix is not configured.", contact_doc, bitrix_data)

    orgid = _first_present(context.get("orgid"), context.get("profile_orgid"))
    email = _empty_to_none(getattr(contact_doc, "email_id", None)) if contact_doc else _empty_to_none(context.get("raised_by"))
    phone = (
        _empty_to_none(getattr(contact_doc, "mobile_no", None) or getattr(contact_doc, "phone", None))
        if contact_doc
        else None
    )
    if not orgid and not email and not phone:
        bitrix_data["status"] = "missing_lookup"
        return _ticket_only_response(context, "Ticket has no Haravan Org ID, email, or phone for Bitrix lookup.", contact_doc, bitrix_data)

    client = BitrixClient(config)
    try:
        company = _first(client.find_companies(haravan_orgid=_empty_to_none(orgid)))
        bitrix_contact = _first(client.find_contacts(email=email, phone=phone))
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Bitrix customer profile fetch failed")
        bitrix_data["status"] = "error"
        return _ticket_only_response(context, "Bitrix fetch failed.", contact_doc, bitrix_data)

    if company:
        company_id = _entity_id(company)
        company_url = client.build_entity_url("company", company_id)
        bitrix_data["company"] = {
            "id": str(company_id) if company_id is not None else None,
            "title": company.get("TITLE") or company.get("NAME"),
            "url": company_url,
            "summary": company,
        }
        responsible = _resolve_responsible_user(client, company)
        if responsible:
            bitrix_data["responsible"] = responsible
            if responsible.get("active") and responsible.get("email"):
                _update_ticket_responsible(str(ticket), responsible["email"])

    if bitrix_contact:
        contact_id = _entity_id(bitrix_contact)
        contact_url = client.build_entity_url("contact", contact_id)
        if contact_doc:
            _set_if_possible(contact_doc, "custom_bitrix_contact_id", contact_id)
            _set_if_possible(contact_doc, "custom_bitrix_contact_url", contact_url)
            _set_if_possible(contact_doc, "custom_bitrix_last_synced_at", now_datetime())
            _save_doc(contact_doc)
        bitrix_data["contact"] = {
            "id": str(contact_id) if contact_id is not None else None,
            "title": _contact_title(bitrix_contact),
            "url": contact_url,
            "summary": bitrix_contact,
        }

    bitrix_data["status"] = "matched" if company or bitrix_contact else "not_found"
    return _ticket_only_response(context, "Bitrix profile loaded.", contact_doc, bitrix_data)


def refresh_customer_profile(
    hd_customer: str,
    contact: str | None = None,
    refresh: bool = True,
    ticket: str | int | None = None,
) -> dict[str, Any]:
    frappe.has_permission("HD Customer", "read", hd_customer, throw=True)
    customer_doc = frappe.get_doc("HD Customer", hd_customer)
    if contact:
        frappe.has_permission("Contact", "read", contact, throw=True)
        contact_doc = frappe.get_doc("Contact", contact)
    else:
        contact_doc = None
    config = get_bitrix_config()
    bitrix_data: dict[str, Any] = {
        "enabled": bool(config.get("enabled")),
        "configured": bool(config.get("configured")),
        "company": None,
        "contact": None,
        "responsible": None,
        "status": "disabled",
    }

    if not config.get("enabled"):
        return _profile_response(customer_doc, contact_doc, bitrix_data, "Bitrix enrichment is disabled.")
    if not config.get("configured"):
        bitrix_data["status"] = "missing_config"
        return _profile_response(customer_doc, contact_doc, bitrix_data, "Bitrix is not configured.")

    client = BitrixClient(config)
    now = now_datetime()
    try:
        company = _first(
            client.find_companies(
                domain=_empty_to_none(getattr(customer_doc, "domain", None)),
                haravan_orgid=_empty_to_none(str(getattr(customer_doc, "custom_haravan_orgid", "") or "")),
            )
        )
        bitrix_contact = _first(
            client.find_contacts(
                email=_empty_to_none(getattr(contact_doc, "email_id", None)) if contact_doc else None,
                phone=_empty_to_none(
                    (getattr(contact_doc, "mobile_no", None) or getattr(contact_doc, "phone", None))
                    if contact_doc
                    else None
                ),
            )
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Bitrix customer profile fetch failed")
        bitrix_data["status"] = "error"
        return _profile_response(customer_doc, contact_doc, bitrix_data, "Bitrix fetch failed.")

    if company:
        company_id = _entity_id(company)
        company_url = client.build_entity_url("company", company_id)
        _set_if_possible(customer_doc, "custom_bitrix_company_id", company_id)
        _set_if_possible(customer_doc, "custom_bitrix_company_url", company_url)
        _set_if_possible(customer_doc, "custom_bitrix_match_confidence", 90)
        _set_if_possible(customer_doc, "custom_bitrix_sync_status", "matched")
        _set_if_possible(customer_doc, "custom_bitrix_last_synced_at", now)
        _save_doc(customer_doc)
        _upsert_customer_data(
            hd_customer=customer_doc.name,
            contact=getattr(contact_doc, "name", None) if contact_doc else None,
            entity_type="company",
            external_id=company_id,
            external_url=company_url,
            payload=company,
            confidence=90,
            match_key="domain_or_haravan_orgid",
        )
        bitrix_data["company"] = {
            "id": str(company_id) if company_id is not None else None,
            "title": company.get("TITLE") or company.get("NAME"),
            "url": company_url,
            "summary": company,
        }
        responsible = _resolve_responsible_user(client, company)
        if responsible:
            bitrix_data["responsible"] = responsible
            if responsible.get("active") and responsible.get("email"):
                _update_ticket_responsible(ticket, responsible["email"])

    if bitrix_contact and contact_doc:
        contact_id = _entity_id(bitrix_contact)
        contact_url = client.build_entity_url("contact", contact_id)
        _set_if_possible(contact_doc, "custom_bitrix_contact_id", contact_id)
        _set_if_possible(contact_doc, "custom_bitrix_contact_url", contact_url)
        _set_if_possible(contact_doc, "custom_bitrix_last_synced_at", now)
        _save_doc(contact_doc)
        _upsert_customer_data(
            hd_customer=customer_doc.name,
            contact=getattr(contact_doc, "name", None),
            entity_type="contact",
            external_id=contact_id,
            external_url=contact_url,
            payload=bitrix_contact,
            confidence=80,
            match_key="email_or_phone",
        )
        bitrix_data["contact"] = {
            "id": str(contact_id) if contact_id is not None else None,
            "title": _contact_title(bitrix_contact),
            "url": contact_url,
            "summary": bitrix_contact,
        }

    bitrix_data["status"] = "matched" if company or bitrix_contact else "not_found"
    return _profile_response(customer_doc, contact_doc, bitrix_data, "Customer profile loaded.")


def _profile_response(
    customer_doc: Any,
    contact_doc: Any | None,
    bitrix_data: dict[str, Any],
    message: str,
    ticket: dict[str, Any] | None = None,
):
    return {
        "success": True,
        "data": {
            "ticket": ticket or {},
            "customer": _customer_summary(customer_doc),
            "contact": _contact_doc_summary(contact_doc),
            "haravan": _haravan_links(getattr(customer_doc, "name", None)),
            "bitrix": bitrix_data,
        },
        "message": message,
    }


def _ticket_only_response(
    context: dict[str, Any],
    message: str,
    contact_doc: Any | None = None,
    bitrix_data: dict[str, Any] | None = None,
):
    contact_doc = contact_doc or (frappe.get_doc("Contact", context["contact"]) if context.get("contact") else None)
    return {
        "success": True,
        "data": {
            "ticket": context,
            "customer": None,
            "contact": _contact_doc_summary(contact_doc),
            "haravan": [],
            "bitrix": bitrix_data or {"enabled": False, "configured": False, "status": "idle"},
        },
        "message": message,
    }


def _stored_bitrix_summary(customer_doc: Any, contact_doc: Any | None) -> dict[str, Any]:
    company_id = getattr(customer_doc, "custom_bitrix_company_id", None)
    contact_id = getattr(contact_doc, "custom_bitrix_contact_id", None) if contact_doc else None
    return {
        "enabled": None,
        "configured": None,
        "company": (
            {
                "id": str(company_id),
                "title": getattr(customer_doc, "customer_name", None),
                "url": getattr(customer_doc, "custom_bitrix_company_url", None),
            }
            if company_id
            else None
        ),
        "contact": (
            {
                "id": str(contact_id),
                "title": getattr(contact_doc, "name", None),
                "url": getattr(contact_doc, "custom_bitrix_contact_url", None),
            }
            if contact_id and contact_doc
            else None
        ),
        "responsible": None,
        "status": getattr(customer_doc, "custom_bitrix_sync_status", None) or "local",
        "cached": True,
    }


def _customer_summary(doc: Any) -> dict[str, Any]:
    return {
        "name": getattr(doc, "name", None),
        "customer_name": getattr(doc, "customer_name", None),
        "domain": getattr(doc, "domain", None),
        "haravan_orgid": getattr(doc, "custom_haravan_orgid", None),
        "myharavan": getattr(doc, "custom_myharavan", None),
        "bitrix_company_id": getattr(doc, "custom_bitrix_company_id", None),
        "bitrix_company_url": getattr(doc, "custom_bitrix_company_url", None),
        "bitrix_sync_status": getattr(doc, "custom_bitrix_sync_status", None),
        "bitrix_last_synced_at": getattr(doc, "custom_bitrix_last_synced_at", None),
    }


def _contact_summary(contact: str) -> dict[str, Any] | None:
    if not contact:
        return None
    return _contact_doc_summary(frappe.get_doc("Contact", contact))


def _contact_doc_summary(doc: Any | None) -> dict[str, Any] | None:
    if not doc:
        return None
    return {
        "name": getattr(doc, "name", None),
        "email_id": getattr(doc, "email_id", None),
        "phone": getattr(doc, "phone", None),
        "mobile_no": getattr(doc, "mobile_no", None),
        "bitrix_contact_id": getattr(doc, "custom_bitrix_contact_id", None),
        "bitrix_contact_url": getattr(doc, "custom_bitrix_contact_url", None),
        "bitrix_last_synced_at": getattr(doc, "custom_bitrix_last_synced_at", None),
    }


def _resolve_responsible_user(client: BitrixClient, company: dict[str, Any]) -> dict[str, Any] | None:
    assigned_by_id = company.get("ASSIGNED_BY_ID")
    if not assigned_by_id:
        return None

    if not client.config.get("responsible_configured"):
        return {
            "id": str(assigned_by_id),
            "active": False,
            "status": "missing_config",
        }

    try:
        user = client.get_user(assigned_by_id)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Bitrix responsible user fetch failed")
        return {
            "id": str(assigned_by_id),
            "active": False,
            "status": "error",
        }

    if not user:
        return {
            "id": str(assigned_by_id),
            "active": False,
            "status": "not_found",
        }

    active = _is_bitrix_active(user.get("ACTIVE"))
    return {
        "id": str(user.get("ID") or assigned_by_id),
        "active": active,
        "email": user.get("EMAIL"),
        "name": _bitrix_user_name(user),
        "user_type": user.get("USER_TYPE"),
        "status": "active" if active else "inactive",
    }


def _update_ticket_responsible(ticket: str | int | None, responsible_email: str) -> bool:
    if not ticket or not responsible_email:
        return False
    try:
        ticket_doc = frappe.get_doc("HD Ticket", ticket)
        _set_if_possible(ticket_doc, "custom_responsible", responsible_email)
        _save_doc(ticket_doc)
        return True
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Bitrix responsible local save failed")
        return False


def _bitrix_user_name(user: dict[str, Any]) -> str | None:
    name = " ".join(str(part).strip() for part in [user.get("NAME"), user.get("LAST_NAME")] if part)
    return name or user.get("EMAIL")


def _is_bitrix_active(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "y", "yes"}
    return bool(value)


def _haravan_links(hd_customer: str | None) -> list[dict[str, Any]]:
    if not hd_customer:
        return []
    return frappe.get_all(
        "Haravan Account Link",
        filters={"hd_customer": hd_customer},
        fields=["user", "email", "haravan_userid", "haravan_orgid", "haravan_orgname", "last_login"],
        limit_page_length=20,
    )


def _upsert_customer_data(
    hd_customer: str,
    contact: str | None,
    entity_type: str,
    external_id: str | int | None,
    external_url: str | None,
    payload: dict[str, Any],
    confidence: int,
    match_key: str,
):
    if not external_id:
        return
    filters = {
        "hd_customer": hd_customer,
        "source": "bitrix",
        "entity_type": entity_type,
        "external_id": str(external_id),
    }
    existing = frappe.db.exists("HD Customer Data", filters)
    doc = frappe.get_doc("HD Customer Data", existing) if existing else frappe.new_doc("HD Customer Data")
    doc.update(
        {
            **filters,
            "contact": contact,
            "external_url": external_url,
            "summary_json": json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
            "match_key": match_key,
            "confidence": confidence,
            "last_synced_at": now_datetime(),
        }
    )
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def _set_if_possible(doc: Any, fieldname: str, value: Any):
    if value is None:
        return
    setter = getattr(doc, "set", None)
    if callable(setter):
        setter(fieldname, value)
    else:
        setattr(doc, fieldname, value)


def _save_doc(doc: Any):
    try:
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Bitrix profile local save failed")


def _first(values: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    return values[0] if values else None


def _entity_id(entity: dict[str, Any]) -> Any:
    return entity.get("ID") or entity.get("id")


def _contact_title(entity: dict[str, Any]) -> str | None:
    parts = [entity.get("NAME"), entity.get("LAST_NAME")]
    title = " ".join(str(part).strip() for part in parts if part)
    return title or entity.get("TITLE")


def _empty_to_none(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _get_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


def _ticket_context(ticket: str | int) -> dict[str, Any] | None:
    frappe.has_permission("HD Ticket", "read", str(ticket), throw=True)
    ticket_row = frappe.db.get_value(
        "HD Ticket",
        ticket,
        ["customer", "contact", "raised_by"],
        as_dict=True,
    )
    if not ticket_row:
        return None

    contact = _get_value(ticket_row, "contact")
    raised_by = _get_value(ticket_row, "raised_by")
    if not contact and raised_by:
        contact = frappe.db.get_value("Contact", {"email_id": raised_by}, "name")

    return {
        "name": str(ticket),
        "customer": _get_value(ticket_row, "customer"),
        "contact": contact,
        "raised_by": raised_by,
        "orgid": _safe_ticket_value(ticket, "custom_orgid"),
        "profile_orgid": _safe_ticket_value(ticket, "custom_haravan_profile_orgid"),
    }


def _safe_ticket_value(ticket: str | int, fieldname: str) -> Any:
    try:
        value = frappe.db.get_value("HD Ticket", ticket, fieldname)
        return _get_value(value, fieldname) if isinstance(value, dict) else value
    except Exception:
        return None


def _first_present(*values: Any) -> str | None:
    for value in values:
        cleaned = _empty_to_none(value)
        if cleaned:
            return cleaned
    return None
