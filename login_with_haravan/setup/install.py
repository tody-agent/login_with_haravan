import json

import frappe
from frappe import _

from login_with_haravan.engines.site_config import (
    HARAVAN_OAUTH_CALLBACK_PATH,
    get_haravan_login_credentials,
    get_haravan_redirect_uri_config,
)

PROVIDER_DOCNAME = "haravan_account"
PROVIDER_NAME = "Haravan Account"
HELPDESK_PRODUCT_SUGGESTION_DOCTYPE = "HD Ticket Product Suggestion"
HELPDESK_TICKET_DOCTYPE = "HD Ticket"
HELPDESK_TICKET_TEMPLATE = "Default"
HELPDESK_PRODUCT_SUGGESTION_FIELDNAME = "custom_product_suggestion"
ONBOARDING_SERVICE_INTERNAL_TYPE = "Onboarding Service"
ONBOARDING_SERVICE_DEPENDS_ON = (
    f'eval:doc.custom_internal_type == "{ONBOARDING_SERVICE_INTERNAL_TYPE}"'
)

HELPDESK_TICKET_CC_FIELD = {
    "fieldname": "custom_cc_emails",
    "label": "CC Emails",
    "fieldtype": "Small Text",
    "insert_after": "contact",
    "description": (
        "Enter CC emails separated by commas. "
        "Example: abc@company.com, xyz@company.com"
    ),
}

HELPDESK_TICKET_CC_TEMPLATE_FIELD = {
    "fieldname": "custom_cc_emails",
    "required": 0,
    "hide_from_customer": 1,
    "placeholder": "abc@company.com, xyz@company.com",
}

HELPDESK_ONBOARDING_SERVICE_FIELDS = [
    {
        "fieldname": "custom_service_group",
        "label": "Nhóm dịch vụ",
        "fieldtype": "Select",
        "insert_after": "custom_product_suggestion",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
    {
        "fieldname": "custom_service_name",
        "label": "Service name",
        "fieldtype": "Select",
        "insert_after": "custom_service_group",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
    {
        "fieldname": "custom_service_line",
        "label": "Service Line",
        "fieldtype": "Select",
        "insert_after": "custom_service_name",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
    {
        "fieldname": "custom_service_onboarding_phrase",
        "label": "Service Onboarding Phrase",
        "fieldtype": "Select",
        "insert_after": "custom_service_line",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
    {
        "fieldname": "custom_service_pricing",
        "label": "Service Pricing",
        "fieldtype": "Currency",
        "insert_after": "custom_service_onboarding_phrase",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
    {
        "fieldname": "custom_service_transaction_id",
        "label": "Service Transaction ID",
        "fieldtype": "Data",
        "insert_after": "custom_service_pricing",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
    {
        "fieldname": "custom_service_vendor",
        "label": "Đối tác cung cấp dịch vụ",
        "fieldtype": "Select",
        "insert_after": "custom_service_transaction_id",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
    {
        "fieldname": "custom_service_payment_status",
        "label": "Trạng thái thanh toán",
        "fieldtype": "Select",
        "insert_after": "custom_service_vendor",
        "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
    },
]

HELPDESK_ONBOARDING_SERVICE_TEMPLATE_FIELDS = [
    {
        "fieldname": field["fieldname"],
        "required": 0,
        "hide_from_customer": 0,
    }
    for field in HELPDESK_ONBOARDING_SERVICE_FIELDS
]

HELPDESK_PROFILE_CUSTOM_FIELDS = {
    "HD Customer": [
        {
            "fieldname": "custom_haravan_orgid",
            "label": "Haravan Org ID",
            "fieldtype": "Int",
            "insert_after": "domain",
        },
        {
            "fieldname": "custom_myharavan",
            "label": "MyHaravan Domain",
            "fieldtype": "Data",
            "insert_after": "custom_haravan_orgid",
        },
        {
            "fieldname": "custom_bitrix_company_id",
            "label": "Bitrix Company ID",
            "fieldtype": "Data",
            "insert_after": "custom_myharavan",
        },
        {
            "fieldname": "custom_bitrix_company_url",
            "label": "Bitrix Company URL",
            "fieldtype": "Data",
            "insert_after": "custom_bitrix_company_id",
        },
        {
            "fieldname": "custom_bitrix_match_confidence",
            "label": "Bitrix Match Confidence",
            "fieldtype": "Percent",
            "insert_after": "custom_bitrix_company_url",
        },
        {
            "fieldname": "custom_bitrix_sync_status",
            "label": "Bitrix Sync Status",
            "fieldtype": "Data",
            "insert_after": "custom_bitrix_match_confidence",
        },
        {
            "fieldname": "custom_bitrix_last_synced_at",
            "label": "Bitrix Last Synced At",
            "fieldtype": "Datetime",
            "insert_after": "custom_bitrix_sync_status",
        },
    ],
    "Contact": [
        {
            "fieldname": "custom_bitrix_contact_id",
            "label": "Bitrix Contact ID",
            "fieldtype": "Data",
            "insert_after": "email_id",
        },
        {
            "fieldname": "custom_bitrix_contact_url",
            "label": "Bitrix Contact URL",
            "fieldtype": "Data",
            "insert_after": "custom_bitrix_contact_id",
        },
        {
            "fieldname": "custom_bitrix_last_synced_at",
            "label": "Bitrix Last Synced At",
            "fieldtype": "Datetime",
            "insert_after": "custom_bitrix_contact_url",
        },
    ],
}


def after_install():
    configure_haravan_social_login()
    configure_customer_profile_metadata()
    configure_helpdesk_product_suggestion_permissions()
    configure_helpdesk_product_suggestion_customer_optional()
    configure_ticket_cc_metadata()
    configure_onboarding_service_ticket_metadata()


def after_migrate():
    configure_haravan_social_login()
    configure_customer_profile_metadata()
    configure_helpdesk_product_suggestion_permissions()
    configure_helpdesk_product_suggestion_customer_optional()
    configure_ticket_cc_metadata()
    configure_onboarding_service_ticket_metadata()





@frappe.whitelist()
def configure_haravan_social_login(
    client_id: str | None = None,
    client_secret: str | None = None,
    enable: int | str | bool | None = None,
):
    explicit_client_secret = client_secret
    doc = _get_or_create_social_login_key()
    credentials = _get_configured_credentials(doc)
    redirect_config = get_haravan_redirect_uri_config(provider_doc=doc)
    redirect_url = _select_social_login_redirect_url(doc, redirect_config)
    client_id = client_id or credentials.get("client_id")
    client_secret = client_secret or credentials.get("client_secret")

    existing_secret = _get_existing_secret(doc)
    should_enable = bool(client_id and (client_secret or existing_secret)) if enable is None else bool(int(enable))

    if should_enable and not client_id:
        frappe.throw(_("Haravan Client ID is required before enabling social login."))
    if should_enable and not (client_secret or existing_secret):
        frappe.throw(_("Haravan Client Secret is required before enabling social login."))

    doc.update(
        {
            "social_login_provider": "Custom",
            "provider_name": PROVIDER_NAME,
            "enable_social_login": 1 if should_enable else 0,
            "base_url": "https://accounts.haravan.com",
            "custom_base_url": 1,
            "authorize_url": "/connect/authorize",
            "access_token_url": "/connect/token",
            "redirect_url": redirect_url,
            "api_endpoint": "/connect/userinfo",
            "api_endpoint_args": None,
            "auth_url_data": json.dumps(
                {
                    "response_mode": "query",
                    "response_type": "code",
                    "scope": "openid profile email org userinfo",
                }
            ),
            "user_id_property": "sub",
            "sign_ups": "Allow",
            "icon": "/assets/frappe/icons/social/frappe.svg",
            "show_in_resource_metadata": 0,
        }
    )

    if client_id:
        doc.client_id = client_id
    client_secret_from_site_config = (
        not explicit_client_secret and credentials.get("client_secret_source") == "site_config"
    )
    if client_secret and not client_secret_from_site_config:
        doc.client_secret = client_secret

    doc.flags.ignore_permissions = True
    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    frappe.db.commit()
    return {
        "success": True,
        "data": {
            "name": doc.name,
            "enabled": bool(doc.enable_social_login),
            "redirect_url": redirect_config["redirect_uri"],
            "redirect_uri_source": redirect_config.get("source"),
            "credential_source": credentials.get("source"),
            "client_id_source": credentials.get("client_id_source"),
            "client_secret_source": credentials.get("client_secret_source"),
            "client_secret_stored_in_doctype": bool(
                client_secret and not client_secret_from_site_config
            ),
        },
        "message": "Haravan social login key configured.",
    }


def _select_social_login_redirect_url(doc, redirect_config: dict[str, str]) -> str:
    # Keep the DocType value relative so Frappe can build the authorize URL from
    # the active request host. Exact fixed domains should live in site_config
    # (`haravan_account_login.redirect_uri`), which Frappe core reads at runtime.
    return HARAVAN_OAUTH_CALLBACK_PATH


def _get_or_create_social_login_key():
    if frappe.db.exists("Social Login Key", PROVIDER_DOCNAME):
        return frappe.get_doc("Social Login Key", PROVIDER_DOCNAME)

    doc = frappe.new_doc("Social Login Key")
    doc.provider_name = PROVIDER_NAME
    return doc


def _get_existing_secret(doc) -> str | None:
    if doc.is_new():
        return None
    return doc.get_password("client_secret", raise_exception=False)


def _get_configured_credentials(provider_doc=None) -> dict:
    # Frappe core get_oauth_keys() looks for f"{provider}_login" = "haravan_account_login".
    # The shorter "haravan_login" and flat keys are accepted for backward compatibility.
    return get_haravan_login_credentials(provider_doc=provider_doc)


@frappe.whitelist()
def configure_customer_profile_metadata():
    """Create custom fields used by Bitrix on-demand customer profiles."""
    created = []
    for dt, fields in HELPDESK_PROFILE_CUSTOM_FIELDS.items():
        if not frappe.db.exists("DocType", dt):
            continue
        for field in fields:
            custom_field_name = f"{dt}-{field['fieldname']}"
            if frappe.db.exists("Custom Field", custom_field_name):
                continue
            doc = frappe.new_doc("Custom Field")
            doc.dt = dt
            doc.update(field)
            doc.flags.ignore_permissions = True
            doc.insert(ignore_permissions=True)
            created.append(custom_field_name)

    if created:
        frappe.db.commit()

    return {
        "success": True,
        "data": {"created": created},
        "message": "Customer profile metadata configured.",
    }


@frappe.whitelist()
def configure_ticket_cc_metadata():
    """Create ticket-level CC metadata used by agent-created tickets and replies."""
    if not frappe.db.exists("DocType", HELPDESK_TICKET_DOCTYPE):
        return {
            "success": True,
            "data": {"configured": False, "reason": "doctype_missing"},
            "message": "HD Ticket DocType is not installed.",
        }

    custom_field_changed = _ensure_custom_field(
        HELPDESK_TICKET_DOCTYPE,
        HELPDESK_TICKET_CC_FIELD,
    )
    template_row_changed = _ensure_ticket_template_field(
        HELPDESK_TICKET_TEMPLATE,
        HELPDESK_TICKET_CC_TEMPLATE_FIELD,
    )

    if custom_field_changed or template_row_changed:
        frappe.clear_cache(doctype=HELPDESK_TICKET_DOCTYPE)
        frappe.clear_cache(doctype="HD Ticket Template")
        frappe.db.commit()

    return {
        "success": True,
        "data": {
            "configured": True,
            "custom_field": f"{HELPDESK_TICKET_DOCTYPE}-{HELPDESK_TICKET_CC_FIELD['fieldname']}",
            "template": HELPDESK_TICKET_TEMPLATE,
            "custom_field_changed": custom_field_changed,
            "template_row_changed": template_row_changed,
        },
        "message": "Ticket CC metadata configured.",
    }


@frappe.whitelist()
def configure_onboarding_service_ticket_metadata():
    """Show paid-service ticket fields only for Onboarding Service tickets."""
    if not frappe.db.exists("DocType", HELPDESK_TICKET_DOCTYPE):
        return {
            "success": True,
            "data": {"configured": False, "reason": "doctype_missing"},
            "message": "HD Ticket DocType is not installed.",
        }

    custom_fields_changed = []
    template_rows_changed = []

    for field in HELPDESK_ONBOARDING_SERVICE_FIELDS:
        if _ensure_custom_field(HELPDESK_TICKET_DOCTYPE, field):
            custom_fields_changed.append(field["fieldname"])

    for row in HELPDESK_ONBOARDING_SERVICE_TEMPLATE_FIELDS:
        if _ensure_ticket_template_field(HELPDESK_TICKET_TEMPLATE, row):
            template_rows_changed.append(row["fieldname"])

    changed = bool(custom_fields_changed or template_rows_changed)
    if changed:
        frappe.clear_cache(doctype=HELPDESK_TICKET_DOCTYPE)
        frappe.clear_cache(doctype="HD Ticket Template")
        frappe.db.commit()

    return {
        "success": True,
        "data": {
            "configured": True,
            "depends_on": ONBOARDING_SERVICE_DEPENDS_ON,
            "custom_fields_changed": custom_fields_changed,
            "template_rows_changed": template_rows_changed,
        },
        "message": "Onboarding service ticket metadata configured.",
    }


@frappe.whitelist()
def configure_helpdesk_product_suggestion_customer_optional():
    """Keep Product Suggestion optional on customer portal templates.

    Agent-created tickets still require this field through the Desk Client Script
    and the server-side Product Suggestion mapping script.
    """
    if not frappe.db.exists("DocType", HELPDESK_TICKET_DOCTYPE):
        return {
            "success": True,
            "data": {"configured": False, "reason": "doctype_missing"},
            "message": "HD Ticket DocType is not installed.",
        }

    custom_field_changed = _ensure_product_suggestion_custom_field_optional()
    template_row_changed = _ensure_ticket_template_field(
        HELPDESK_TICKET_TEMPLATE,
        {"fieldname": HELPDESK_PRODUCT_SUGGESTION_FIELDNAME, "required": 0},
    )

    if custom_field_changed or template_row_changed:
        frappe.clear_cache(doctype=HELPDESK_TICKET_DOCTYPE)
        frappe.clear_cache(doctype="HD Ticket Template")
        frappe.db.commit()

    return {
        "success": True,
        "data": {
            "configured": True,
            "fieldname": HELPDESK_PRODUCT_SUGGESTION_FIELDNAME,
            "custom_field_changed": custom_field_changed,
            "template_row_changed": template_row_changed,
        },
        "message": "Product Suggestion is optional for customer ticket templates.",
    }


def _ensure_product_suggestion_custom_field_optional() -> bool:
    custom_field_name = (
        f"{HELPDESK_TICKET_DOCTYPE}-{HELPDESK_PRODUCT_SUGGESTION_FIELDNAME}"
    )
    if not frappe.db.exists("Custom Field", custom_field_name):
        return False

    doc = frappe.get_doc("Custom Field", custom_field_name)
    if not int(getattr(doc, "reqd", 0) or 0):
        return False

    doc.reqd = 0
    doc.flags.ignore_permissions = True
    doc.save(ignore_permissions=True)
    return True


def _ensure_custom_field(doctype: str, field: dict[str, object]) -> bool:
    custom_field_name = f"{doctype}-{field['fieldname']}"
    existing = frappe.db.exists("Custom Field", custom_field_name)
    doc = (
        frappe.get_doc("Custom Field", custom_field_name)
        if existing
        else frappe.new_doc("Custom Field")
    )

    values = {"dt": doctype, **field}
    changed = not bool(existing)
    for key, value in values.items():
        if getattr(doc, key, None) != value:
            changed = True

    if not changed:
        return False

    doc.update(values)
    doc.flags.ignore_permissions = True
    if existing:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    return True


def _ensure_ticket_template_field(template: str, row: dict[str, object]) -> bool:
    if not frappe.db.exists("HD Ticket Template", template):
        return False

    filters = {
        "parent": template,
        "parenttype": "HD Ticket Template",
        "parentfield": "fields",
        "fieldname": row["fieldname"],
    }
    existing = frappe.db.exists("HD Ticket Template Field", filters)
    if existing:
        doc = frappe.get_doc("HD Ticket Template Field", existing)
        changed = False
        for key, value in row.items():
            if getattr(doc, key, None) != value:
                setattr(doc, key, value)
                changed = True
        if changed:
            doc.flags.ignore_permissions = True
            doc.save(ignore_permissions=True)
        return changed

    template_doc = frappe.get_doc("HD Ticket Template", template)
    template_doc.append("fields", row)
    template_doc.flags.ignore_permissions = True
    template_doc.save(ignore_permissions=True)
    return True


@frappe.whitelist()
def configure_helpdesk_product_suggestion_permissions():
    """Allow every user to read/select product suggestions on the ticket form."""
    if not frappe.db.exists("DocType", HELPDESK_PRODUCT_SUGGESTION_DOCTYPE):
        return {
            "success": True,
            "data": {"configured": False, "reason": "doctype_missing"},
            "message": "HD Ticket Product Suggestion DocType is not installed.",
        }

    changed = _ensure_custom_docperm(
        HELPDESK_PRODUCT_SUGGESTION_DOCTYPE,
        role="All",
        permissions={"read": 1, "select": 1},
    )

    if changed:
        frappe.clear_cache(doctype=HELPDESK_PRODUCT_SUGGESTION_DOCTYPE)
        frappe.db.commit()

    return {
        "success": True,
        "data": {
            "configured": True,
            "doctype": HELPDESK_PRODUCT_SUGGESTION_DOCTYPE,
            "role": "All",
            "permissions": ["read", "select"],
            "changed": changed,
        },
        "message": "HD Ticket Product Suggestion permissions configured.",
    }


def _ensure_custom_docperm(doctype: str, role: str, permissions: dict[str, int]) -> bool:
    filters = {"parent": doctype, "role": role, "permlevel": 0}
    docname = frappe.db.exists("Custom DocPerm", filters)
    if docname:
        doc = frappe.get_doc("Custom DocPerm", docname)
    else:
        doc = frappe.new_doc("Custom DocPerm")
        doc.parent = doctype
        doc.parenttype = "DocType"
        doc.parentfield = "permissions"
        doc.role = role
        doc.permlevel = 0

    changed = not docname
    for fieldname, value in permissions.items():
        if int(doc.get(fieldname) or 0) != int(value):
            doc.set(fieldname, value)
            changed = True

    if not changed:
        return False

    doc.flags.ignore_permissions = True
    if docname:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    return True
