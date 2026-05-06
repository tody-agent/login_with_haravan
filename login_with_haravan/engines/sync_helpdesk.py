"""Sync Haravan identity data into Frappe Helpdesk entities.

Handles upsert of HD Customer, Contact, and User profile links after
successful Haravan OAuth login.

HD Customer field mapping (production):
  - customer_name (str): "[OrgName] - [OrgID]"
  - custom_haravan_orgid (Int): Haravan organization ID
  - domain (str): e.g. "shopname.myharavan.com"
  - custom_myharavan (str): MyHaravan subdomain

Role-based Contact → HD Customer linking:
  - owner, admin → Contact linked to HD Customer → sees ALL org tickets
  - staff (or other) → Contact NOT linked → sees only OWN tickets
"""

import json
import re

import frappe

# Haravan roles that grant org-wide ticket visibility via Contact → HD Customer link.
# owner/admin can see ALL tickets of their Haravan org in the Helpdesk portal.
# Staff users only see tickets they created themselves.
HD_CUSTOMER_LINK_ROLES = {"owner", "admin"}
MIN_PHONE_DIGITS = 7

def enrich_helpdesk_data(user: str, profile: dict):
    """Main entry point — called from oauth._persist_after_login().

    Creates/updates only native Helpdesk identity links from Haravan login
    claims. Rich customer profile data is fetched from Bitrix on demand.
    """
    from login_with_haravan.engines.haravan_identity import normalize_haravan_profile

    normalized = normalize_haravan_profile(profile)

    # 1. Update User profile (middle_name, locale → language)
    update_user_profile(user, normalized)

    # 2. Upsert HD Customer from Haravan org
    hd_customer_name = upsert_hd_customer(normalized)

    # 3. Upsert Contact — only link to HD Customer if user has manager role
    if normalized.get("email"):
        user_roles = set(normalized.get("role", []))
        should_link = bool(user_roles & HD_CUSTOMER_LINK_ROLES)
        upsert_contact(
            normalized,
            hd_customer_name if should_link else None,
        )

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
    """Build deterministic HD Customer name: '[OrgName] - [OrgID]'."""
    return f"{org_name} - {org_id}"


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

    Naming: ``{orgname} - {orgid}`` (e.g. ``Minh Hải Store - 12345``).
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
    """HD Ticket before_insert hook — auto-set and validate customer context.

    If user has exactly 1 linked HD Customer and the ticket has no customer set,
    automatically assign it.
    """
    if not doc.customer:
        user = frappe.session.user
        if user and user != "Guest":
            links = frappe.get_all(
                "Haravan Account Link",
                filters={"user": user},
                fields=["hd_customer"],
            )
            customers = [l.hd_customer for l in links if l.hd_customer]
            unique_customers = list(set(customers))

            if len(unique_customers) == 1:
                doc.customer = unique_customers[0]

    validate_portal_ticket_customer_or_store_url(doc)


def validate_portal_ticket_customer_or_store_url(doc, method=None):
    """Require customer context for tickets created from the customer portal."""
    if not getattr(doc, "via_customer_portal", None):
        return

    submitted_doc = _submitted_ticket_doc()
    customer = str(
        _dict_value(submitted_doc, "customer", getattr(doc, "customer", None)) or ""
    ).strip()
    store_url = str(
        _dict_value(submitted_doc, "custom_store_url", getattr(doc, "custom_store_url", None)) or ""
    ).strip()
    if customer or store_url:
        return

    frappe.throw(
        "Vui lòng chọn Customer hoặc nhập Link Web / MyHaravan trước khi tạo ticket.",
        title="Thiếu thông tin khách hàng",
    )


def _submitted_ticket_doc() -> dict:
    form_dict = getattr(frappe, "form_dict", None)
    raw_doc = form_dict.get("doc") if form_dict else None
    if isinstance(raw_doc, dict):
        return raw_doc
    if isinstance(raw_doc, str):
        try:
            parsed = json.loads(raw_doc)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _dict_value(data: dict, key: str, fallback=None):
    if isinstance(data, dict) and key in data:
        return data.get(key)
    return fallback


def get_contact_phone_options(contact: str | None) -> list[str]:
    """Return Contact phone suggestions from the main Contact fields."""
    if not contact:
        return []

    doc = frappe.get_doc("Contact", contact)
    candidates = [
        getattr(doc, "mobile_no", None),
        getattr(doc, "phone", None),
    ]
    options = []
    seen = set()
    for phone in candidates:
        key = normalize_phone_key(phone)
        if not key or key in seen:
            continue
        seen.add(key)
        options.append(str(phone).strip())
    return options


def persist_ticket_contact_phone(doc, method=None):
    """Store a newly-entered ticket phone on the ticket Contact for future suggestions."""
    phone = _doc_value(doc, "custom_phone")
    key = normalize_phone_key(phone)
    if not key:
        return

    contact_name = _doc_value(doc, "contact") or _contact_for_email(
        _doc_value(doc, "raised_by")
    )
    if not contact_name:
        return

    try:
        contact = frappe.get_doc("Contact", contact_name)
        existing = _contact_phone_keys(contact)
        if key in existing:
            return

        cleaned_phone = str(phone).strip()
        if not getattr(contact, "mobile_no", None):
            contact.mobile_no = cleaned_phone
        if not getattr(contact, "phone", None):
            contact.phone = cleaned_phone
        contact.flags.ignore_permissions = True
        contact.save(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Haravan ticket contact phone sync failed")


def normalize_phone_key(phone) -> str:
    """Normalize phone text for duplicate checks without changing stored formatting."""
    digits = re.sub(r"\D+", "", str(phone or ""))
    if digits.startswith("0084") and len(digits) > 6:
        digits = "0" + digits[4:]
    elif digits.startswith("84") and len(digits) >= 11:
        digits = "0" + digits[2:]
    return digits if len(digits) >= MIN_PHONE_DIGITS else ""


def _contact_for_email(email: str | None) -> str | None:
    email = str(email or "").strip()
    if not email:
        return None
    return frappe.db.get_value("Contact", {"email_id": email}, "name")


def _doc_value(doc, key: str):
    getter = getattr(doc, "get", None)
    if callable(getter):
        value = getter(key)
        if value is not None:
            return value
    return getattr(doc, key, None)


def _contact_phone_keys(contact) -> set[str]:
    return {
        key
        for key in [
            normalize_phone_key(getattr(contact, "mobile_no", None)),
            normalize_phone_key(getattr(contact, "phone", None)),
        ]
        if key
    }
