import frappe

from login_with_haravan.engines.sync_helpdesk import persist_ticket_contact_phone


PHONE_FIELD_CANDIDATES = ("custom_contact_phone", "custom_phone", "contact_phone")


def execute():
    """Backfill Contact phone fields from already-created Helpdesk tickets."""
    if not frappe.db.exists("DocType", "HD Ticket"):
        return

    try:
        phone_fields = _ticket_phone_fields()
        if not phone_fields:
            return

        tickets = frappe.get_all(
            "HD Ticket",
            fields=["name", "contact", "raised_by", *phone_fields],
            or_filters=[[field, "!=", ""] for field in phone_fields],
        )
        for ticket in tickets:
            persist_ticket_contact_phone(ticket)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Haravan backfill contact phone from tickets failed",
        )


def _ticket_phone_fields() -> list[str]:
    meta = frappe.get_meta("HD Ticket")
    return [field for field in PHONE_FIELD_CANDIDATES if meta.has_field(field)]
