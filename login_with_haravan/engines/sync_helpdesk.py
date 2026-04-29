"""Sync Haravan identity data into Frappe Helpdesk entities.

Handles upsert of HD Customer, Contact, and User profile enrichment
after successful Haravan OAuth login.

HD Customer field mapping (production):
  - customer_name (str): "[OrgID] - [OrgName]"
  - custom_haravan_orgid (Int): Haravan organization ID
  - domain (str): e.g. "shopname.myharavan.com"
  - custom_myharavan (str): MyHaravan subdomain
  - custom_shopplan_name (str): e.g. "Scale", "Growth"
  - custom_customer_segment (Select): "SME" | "Medium" | "Enterprise"
  - custom_hsi_segment (Select): "0" | "1" | "100" | "200" | "500" | "500+"
  - custom_first_paid_date (Datetime): first paid timestamp
"""

import frappe
from frappe.utils import now_datetime
from datetime import datetime

def _format_haravan_date(iso_str: str) -> str | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # Convert to local server timezone
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def enrich_helpdesk_data(user: str, profile: dict):
    """Main entry point — called from oauth._persist_after_login().

    Creates/updates HD Customer, Contact, and User records based on
    the normalized Haravan profile.
    """
    from login_with_haravan.engines.haravan_identity import normalize_haravan_profile

    normalized = normalize_haravan_profile(profile)

    # 1. Update User profile (middle_name, locale → language)
    update_user_profile(user, normalized)

    # 2. Upsert HD Customer from Haravan org
    hd_customer_name = upsert_hd_customer(normalized)

    # 3. Upsert Contact and link to HD Customer
    if normalized.get("email"):
        upsert_contact(normalized, hd_customer_name)

    return hd_customer_name


def update_user_profile(user: str, normalized: dict):
    """Update Frappe User doc with Haravan profile fields (only if empty)."""
    if not frappe.db.exists("User", user):
        return

    user_doc = frappe.get_doc("User", user)
    changed = False

    if normalized.get("middle_name") and not user_doc.middle_name:
        user_doc.middle_name = normalized["middle_name"]
        changed = True

    if normalized.get("locale") and not user_doc.language:
        user_doc.language = normalized["locale"]
        changed = True

    if changed:
        user_doc.flags.ignore_permissions = True
        user_doc.save(ignore_permissions=True)


def _make_hd_customer_name(org_id, org_name: str) -> str:
    """Build deterministic HD Customer name: '[OrgID] - [OrgName]'."""
    return f"{org_id} - {org_name}"


def _safe_int(value) -> int | None:
    """Convert value to int safely, return None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def upsert_hd_customer(normalized: dict) -> str | None:
    """Create or update an HD Customer record for a Haravan organization.

    Naming: ``{orgid} - {orgname}`` (e.g. ``12345 - Minh Hải Store``).
    Primary lookup is by ``custom_haravan_orgid`` (Int field) for deterministic matching.

    Returns the HD Customer name (document ID) or None if orgid/orgname missing.
    """
    org_id = normalized.get("orgid")
    org_name = normalized.get("orgname")

    if not org_id or not org_name:
        return None

    org_id_int = _safe_int(org_id)
    candidate_name = _make_hd_customer_name(org_id, org_name)

    # Primary lookup: by custom_haravan_orgid (handles org renames gracefully)
    if org_id_int is not None:
        existing_by_orgid = frappe.db.get_value(
            "HD Customer",
            {"custom_haravan_orgid": org_id_int},
            "name",
            cache=False,
        )
        if existing_by_orgid:
            _update_hd_customer_metadata(existing_by_orgid, normalized, candidate_name)
            return existing_by_orgid

    # Fallback: by exact candidate_name
    existing = frappe.db.get_value(
        "HD Customer", candidate_name, "name", cache=False
    )
    if existing:
        _update_hd_customer_metadata(existing, normalized, candidate_name)
        return existing

    # Create new HD Customer
    try:
        doc = frappe.new_doc("HD Customer")
        doc.customer_name = candidate_name
        doc.domain = f"{org_id}.myharavan.com"
        doc.custom_haravan_orgid = org_id_int
        doc.custom_myharavan = f"{org_id}.myharavan.com"

        org_data = normalized.get("haravan_org_data", {})
        if org_data.get("display_plan_name"):
            doc.custom_shopplan_name = org_data.get("display_plan_name")
        first_paid_date = org_data.get("subscription_created_at")
        if first_paid_date:
            formatted_date = _format_haravan_date(first_paid_date)
            if formatted_date:
                doc.custom_first_paid_date = formatted_date

        doc.flags.ignore_permissions = True
        doc.insert(ignore_permissions=True)
        return doc.name
    except Exception as e:
        frappe.log_error(
            f"Failed to create HD Customer for org {org_id}: {e}",
            "Haravan Sync Error",
        )
        return None


def _update_hd_customer_metadata(
    customer_name: str, normalized: dict, expected_name: str | None = None
):
    """Update HD Customer fields that may have changed."""
    try:
        doc = frappe.get_doc("HD Customer", customer_name)
        changed = False

        org_id = normalized.get("orgid", "")
        org_id_int = _safe_int(org_id)
        domain = f"{org_id}.myharavan.com" if org_id else ""

        if domain and not doc.domain:
            doc.domain = domain
            changed = True

        if org_id_int is not None and not doc.custom_haravan_orgid:
            doc.custom_haravan_orgid = org_id_int
            changed = True

        if domain and not doc.custom_myharavan:
            doc.custom_myharavan = domain
            changed = True

        org_data = normalized.get("haravan_org_data", {})
        plan_name = org_data.get("display_plan_name")
        if plan_name and doc.custom_shopplan_name != plan_name:
            doc.custom_shopplan_name = plan_name
            changed = True

        first_paid_date = org_data.get("subscription_created_at")
        if first_paid_date and not doc.custom_first_paid_date:
            formatted_date = _format_haravan_date(first_paid_date)
            if formatted_date:
                doc.custom_first_paid_date = formatted_date
                changed = True

        if changed:
            doc.flags.ignore_permissions = True
            doc.save(ignore_permissions=True)
    except Exception:
        pass  # Non-critical — don't block login


def upsert_contact(normalized: dict, hd_customer_name: str | None):
    """Create or update a Contact and link it to the HD Customer."""
    email = normalized.get("email")
    if not email:
        return

    contact_name = frappe.db.get_value("Contact", {"email_id": email}, "name")

    if not contact_name:
        _create_contact(normalized, hd_customer_name)
    else:
        _update_contact(contact_name, normalized, hd_customer_name)


def _create_contact(normalized: dict, hd_customer_name: str | None):
    """Create a new Contact with email and optional HD Customer link."""
    email = normalized["email"]
    try:
        contact = frappe.new_doc("Contact")
        contact.first_name = normalized.get("name") or email.split("@")[0]
        contact.middle_name = normalized.get("middle_name") or ""
        contact.add_email(email, is_primary=True)

        if hd_customer_name:
            contact.append("links", {
                "link_doctype": "HD Customer",
                "link_name": hd_customer_name,
            })

        contact.flags.ignore_permissions = True
        contact.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(
            f"Failed to create Contact for {email}: {e}",
            "Haravan Sync Error",
        )


def _update_contact(contact_name: str, normalized: dict, hd_customer_name: str | None):
    """Update existing Contact — add HD Customer link if missing."""
    try:
        contact = frappe.get_doc("Contact", contact_name)
        changed = False

        # Ensure HD Customer link exists (multi-org support)
        if hd_customer_name:
            link_exists = any(
                link.link_doctype == "HD Customer" and link.link_name == hd_customer_name
                for link in contact.links
            )
            if not link_exists:
                contact.append("links", {
                    "link_doctype": "HD Customer",
                    "link_name": hd_customer_name,
                })
                changed = True

        # Fill middle_name if missing
        if not contact.middle_name and normalized.get("middle_name"):
            contact.middle_name = normalized["middle_name"]
            changed = True

        if changed:
            contact.flags.ignore_permissions = True
            contact.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(
            f"Failed to update Contact {contact_name}: {e}",
            "Haravan Sync Error",
        )


def auto_set_customer(doc, method=None):
    """HD Ticket before_insert hook — auto-set customer from user's linked HD Customers.

    If user has exactly 1 linked HD Customer and the ticket has no customer set,
    automatically assign it.
    """
    if doc.customer:
        return

    user = frappe.session.user
    if not user or user == "Guest":
        return

    links = frappe.get_all(
        "Haravan Account Link",
        filters={"user": user},
        fields=["hd_customer"],
    )
    customers = [l.hd_customer for l in links if l.hd_customer]
    unique_customers = list(set(customers))

    if len(unique_customers) == 1:
        doc.customer = unique_customers[0]
