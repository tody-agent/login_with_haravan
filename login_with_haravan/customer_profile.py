"""Whitelisted APIs for the Bitrix-backed Helpdesk customer profile panel."""

import frappe

from login_with_haravan.engines.customer_enrichment import (
    get_ticket_customer_profile as build_ticket_customer_profile,
    refresh_customer_profile as refresh_hd_customer_profile,
)


@frappe.whitelist()
def get_ticket_customer_profile(ticket: str | int, refresh: int | str | bool = 0):
    return build_ticket_customer_profile(ticket, refresh=_as_bool(refresh))


@frappe.whitelist()
def refresh_customer_profile(hd_customer: str, contact: str | None = None):
    # SECURITY: Explicitly verify permissions to prevent IDOR since
    # frappe.get_doc() inside engines/customer_enrichment.py does not enforce them.
    frappe.has_permission("HD Customer", "read", hd_customer, throw=True)
    if contact:
        frappe.has_permission("Contact", "read", contact, throw=True)
    return refresh_hd_customer_profile(hd_customer, contact, refresh=True)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
