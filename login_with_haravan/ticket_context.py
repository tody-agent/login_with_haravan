"""Whitelisted APIs for Helpdesk ticket create-form personalization."""

import frappe

from login_with_haravan.engines.ticket_autofill import (
    get_ticket_autofill_metadata,
    resolve_ticket_autofill,
)


@frappe.whitelist()
def get_create_ticket_metadata():
    return {
        "success": True,
        "data": get_ticket_autofill_metadata(),
        "message": "Ticket create metadata loaded.",
    }


@frappe.whitelist()
def resolve_create_ticket_context(link_web_myharavan=None, product_suggestion=None):
    return {
        "success": True,
        "data": resolve_ticket_autofill(link_web_myharavan, product_suggestion),
        "message": "Ticket context resolved.",
    }
