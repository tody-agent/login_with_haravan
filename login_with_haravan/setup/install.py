import json

import frappe
from frappe import _

from login_with_haravan.engines.site_config import (
    HARAVAN_OAUTH_CALLBACK_PATH,
    get_haravan_login_credentials,
    get_haravan_redirect_uri_config,
)
from login_with_haravan.setup.template_safety import escape_template_context

PROVIDER_DOCNAME = "haravan_account"
PROVIDER_NAME = "Haravan Account"
HARAVAN_SOCIAL_ICON_URL = "https://haravandesk.s.frappe.cloud/files/haravan_favicon_24.png"
HDTICKET_PHONE_CLIENT_SCRIPT_NAME = "Haravan HD Ticket Phone Client Script"
HDTICKET_PHONE_SERVER_SCRIPT_NAME = "Haravan HD Ticket Phone Server Script"
HDTICKET_TEMPLATE_DOCTYPE = "HD Ticket Template"
HDTICKET_TEMPLATE_DOCNAME = "Default"
HELPDESK_PRODUCT_SUGGESTION_DOCTYPE = "HD Ticket Product Suggestion"
HELPDESK_TICKET_DOCTYPE = "HD Ticket"
HELPDESK_INTEGRATIONS_SETTINGS_DOCTYPE = "Helpdesk Integrations Settings"
HELPDESK_TICKET_TEMPLATE = "Default"
HELPDESK_TICKET_CUSTOMER_FIELDNAME = "customer"
HELPDESK_PRODUCT_SUGGESTION_FIELDNAME = "custom_product_suggestion"
HELPDESK_TICKET_RESPONSIBLE_FIELDNAME = "custom_responsible"
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

HELPDESK_TICKET_CUSTOMER_TEMPLATE_FIELD = {
    "fieldname": HELPDESK_TICKET_CUSTOMER_FIELDNAME,
    "idx": 2,
    "required": 0,
    "hide_from_customer": 0,
    "placeholder": "Chọn HD Customer nhận ticket",
    "url_method": "login_with_haravan.oauth.get_user_haravan_org_options",
}

HELPDESK_TICKET_RESPONSIBLE_FIELD = {
    "fieldname": HELPDESK_TICKET_RESPONSIBLE_FIELDNAME,
    "label": "Người phụ trách Bitrix",
    "fieldtype": "Data",
    "insert_after": "contact",
    "read_only": 1,
    "description": "Email người phụ trách lấy từ Bitrix user.get theo ASSIGNED_BY_ID.",
}

HELPDESK_INTEGRATIONS_BITRIX_FIELDS = [
    {
        "fieldname": "bitrix_customer_api_section",
        "label": "Bitrix - Customer API (crm.company)",
        "fieldtype": "Section Break",
    },
    {
        "fieldname": "bitrix_enabled",
        "label": "Bitrix Enabled",
        "fieldtype": "Check",
        "insert_after": "bitrix_customer_api_section",
        "default": "1",
        "description": "Bật/tắt lấy hồ sơ customer/company từ Bitrix.",
    },
    {
        "fieldname": "bitrix_webhook_url",
        "label": "Bitrix Customer Inbound Webhook URL",
        "fieldtype": "Password",
        "insert_after": "bitrix_enabled",
        "description": (
            "Customer/company API. Dùng để gọi crm.company.* lấy hồ sơ khách hàng. "
            "Tạo trong Bitrix24 > Applications > Developer resources > Inbound webhook "
            "với scope crm. Ví dụ: https://haravan.bitrix24.vn/rest/57792/{customer_secret_key}/"
        ),
    },
    {
        "fieldname": "bitrix_responsible_api_section",
        "label": "Bitrix - Responsible API (user.get)",
        "fieldtype": "Section Break",
        "insert_after": "bitrix_webhook_url",
    },
    {
        "fieldname": "bitrix_responsible_webhook_url",
        "label": "Bitrix Responsible Inbound Webhook URL",
        "fieldtype": "Password",
        "insert_after": "bitrix_responsible_api_section",
        "description": (
            "Responsible/user API. Dùng để gọi user.get theo ASSIGNED_BY_ID và cập nhật "
            "HD Ticket.custom_responsible khi ACTIVE=true. Tạo inbound webhook riêng trong "
            "Bitrix24 với scope user_basic. Có thể nhập base webhook .../rest/57792/secret/ "
            "hoặc full template .../user.get.json?ID={ASSIGNED_BY_ID}."
        ),
    },
    {
        "fieldname": "bitrix_portal_url",
        "label": "Bitrix Portal URL",
        "fieldtype": "Data",
        "insert_after": "bitrix_responsible_webhook_url",
        "description": "URL portal dùng để build link mở Bitrix, ví dụ https://haravan.bitrix24.vn.",
    },
    {
        "fieldname": "bitrix_timeout_seconds",
        "label": "Bitrix Timeout Seconds",
        "fieldtype": "Int",
        "insert_after": "bitrix_portal_url",
        "default": "15",
    },
    {
        "fieldname": "bitrix_refresh_ttl_minutes",
        "label": "Bitrix Refresh TTL Minutes",
        "fieldtype": "Int",
        "insert_after": "bitrix_timeout_seconds",
        "default": "60",
    },
]

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
        "hide_from_customer": 1,
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
    configure_helpdesk_integrations_settings_metadata()
    configure_helpdesk_product_suggestion_permissions()
    configure_ticket_customer_template_metadata()
    configure_helpdesk_product_suggestion_customer_optional()
    configure_ticket_cc_metadata()
    configure_onboarding_service_ticket_metadata()
    _warn_helpdesk_auto_provision_deprecated("after_install")
    ensure_default_hd_ticket_template()


def after_migrate():
    configure_haravan_social_login()
    configure_customer_profile_metadata()
    configure_helpdesk_integrations_settings_metadata()
    configure_helpdesk_product_suggestion_permissions()
    configure_ticket_customer_template_metadata()
    configure_helpdesk_product_suggestion_customer_optional()
    configure_ticket_cc_metadata()
    configure_onboarding_service_ticket_metadata()
    _warn_helpdesk_auto_provision_deprecated("after_migrate")
    ensure_default_hd_ticket_template()





@frappe.whitelist()
def configure_haravan_social_login(
    client_id: str | None = None,
    client_secret: str | None = None,
    enable: int | str | bool | None = None,
):
    frappe.only_for("System Manager")
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
            "icon": HARAVAN_SOCIAL_ICON_URL,
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
    frappe.only_for("System Manager")
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

    if frappe.db.exists("DocType", HELPDESK_TICKET_DOCTYPE):
        if _ensure_custom_field(HELPDESK_TICKET_DOCTYPE, HELPDESK_TICKET_RESPONSIBLE_FIELD):
            created.append(f"{HELPDESK_TICKET_DOCTYPE}-{HELPDESK_TICKET_RESPONSIBLE_FIELDNAME}")

    if created:
        frappe.db.commit()

    return {
        "success": True,
        "data": {"created": created},
        "message": "Customer profile metadata configured.",
    }


@frappe.whitelist()
def configure_helpdesk_integrations_settings_metadata():
    """Create Bitrix config fields on Helpdesk Integrations Settings."""
    frappe.only_for("System Manager")
    if not frappe.db.exists("DocType", HELPDESK_INTEGRATIONS_SETTINGS_DOCTYPE):
        return {
            "success": True,
            "data": {"configured": False, "reason": "doctype_missing"},
            "message": "Helpdesk Integrations Settings DocType is not installed.",
        }

    changed_fields = []
    skipped_existing_fields = []
    for field in HELPDESK_INTEGRATIONS_BITRIX_FIELDS:
        fieldname = str(field["fieldname"])
        custom_field_name = f"{HELPDESK_INTEGRATIONS_SETTINGS_DOCTYPE}-{fieldname}"
        if not frappe.db.exists("Custom Field", custom_field_name) and _doctype_has_field(
            HELPDESK_INTEGRATIONS_SETTINGS_DOCTYPE,
            fieldname,
        ):
            if _ensure_standard_field_properties(
                HELPDESK_INTEGRATIONS_SETTINGS_DOCTYPE,
                field,
            ):
                changed_fields.append(fieldname)
            skipped_existing_fields.append(fieldname)
            continue
        if _ensure_custom_field(HELPDESK_INTEGRATIONS_SETTINGS_DOCTYPE, field):
            changed_fields.append(fieldname)

    if changed_fields:
        frappe.clear_cache(doctype=HELPDESK_INTEGRATIONS_SETTINGS_DOCTYPE)
        frappe.db.commit()

    return {
        "success": True,
        "data": {
            "configured": True,
            "changed_fields": changed_fields,
            "skipped_existing_fields": skipped_existing_fields,
        },
        "message": "Helpdesk Integrations Settings Bitrix fields configured.",
    }


@frappe.whitelist()
def configure_ticket_customer_template_metadata():
    """Show the HD Customer field on the customer portal ticket template."""
    frappe.only_for("System Manager")
    if not frappe.db.exists("DocType", HELPDESK_TICKET_DOCTYPE):
        return {
            "success": True,
            "data": {"configured": False, "reason": "doctype_missing"},
            "message": "HD Ticket DocType is not installed.",
        }

    template_row_changed = _ensure_ticket_template_field(
        HELPDESK_TICKET_TEMPLATE,
        HELPDESK_TICKET_CUSTOMER_TEMPLATE_FIELD,
    )

    if template_row_changed:
        frappe.clear_cache(doctype=HELPDESK_TICKET_DOCTYPE)
        frappe.clear_cache(doctype="HD Ticket Template")
        frappe.db.commit()

    return {
        "success": True,
        "data": {
            "configured": True,
            "fieldname": HELPDESK_TICKET_CUSTOMER_FIELDNAME,
            "template": HELPDESK_TICKET_TEMPLATE,
            "template_row_changed": template_row_changed,
        },
        "message": "HD Customer is visible on customer ticket templates.",
    }


@frappe.whitelist()
def configure_ticket_cc_metadata():
    """Create ticket-level CC metadata used by agent-created tickets and replies."""
    frappe.only_for("System Manager")
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
    """Keep paid-service ticket fields internal to agents."""
    frappe.only_for("System Manager")
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
    frappe.only_for("System Manager")
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


def _doctype_has_field(doctype: str, fieldname: str) -> bool:
    try:
        meta = frappe.get_meta(doctype)
        has_field = getattr(meta, "has_field", None)
        if callable(has_field):
            return bool(has_field(fieldname))
    except Exception:
        return False
    return False


def _ensure_standard_field_properties(doctype: str, field: dict[str, object]) -> bool:
    changed = False
    fieldname = str(field["fieldname"])
    for prop in ("label", "description"):
        if prop in field and _ensure_property_setter(doctype, fieldname, prop, str(field[prop])):
            changed = True
    return changed


def _ensure_property_setter(doctype: str, fieldname: str, prop: str, value: str) -> bool:
    filters = {
        "doc_type": doctype,
        "doctype_or_field": "DocField",
        "field_name": fieldname,
        "property": prop,
    }
    existing = frappe.db.exists("Property Setter", filters)
    doc = (
        frappe.get_doc("Property Setter", existing)
        if existing
        else frappe.new_doc("Property Setter")
    )
    values = {
        **filters,
        "property_type": "Text",
        "value": value,
    }
    changed = not bool(existing)
    for key, new_value in values.items():
        if getattr(doc, key, None) != new_value:
            setattr(doc, key, new_value)
            changed = True

    if not changed:
        return False

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
    frappe.only_for("System Manager")
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

def _warn_helpdesk_auto_provision_deprecated(trigger: str):
    message = (
        "HD Ticket auto provisioning is deprecated and no longer runs in "
        f"{trigger}. Run `bench --site <site> execute "
        "login_with_haravan.setup.install.ensure_helpdesk_phone_scripts` manually if needed."
    )
    logger_factory = getattr(frappe, "logger", None)
    if callable(logger_factory):
        logger_factory("login_with_haravan").warning(message)


def ensure_default_hd_ticket_template() -> dict:
    """Create the default template once and never overwrite existing config."""
    if not frappe.db.exists("DocType", HDTICKET_TEMPLATE_DOCTYPE):
        return {"success": False, "status": "doctype_missing"}

    if frappe.db.exists(HDTICKET_TEMPLATE_DOCTYPE, HDTICKET_TEMPLATE_DOCNAME):
        return {"success": True, "status": "skipped_existing", "name": HDTICKET_TEMPLATE_DOCNAME}

    doc = frappe.new_doc(HDTICKET_TEMPLATE_DOCTYPE)
    payload = _build_default_hd_ticket_template_payload()
    for fieldname, value in payload.items():
        if _has_meta_field(HDTICKET_TEMPLATE_DOCTYPE, fieldname):
            doc.set(fieldname, value)

    doc.name = HDTICKET_TEMPLATE_DOCNAME
    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True
    doc.insert(ignore_permissions=True, ignore_mandatory=True)

    return {"success": True, "status": "created", "name": doc.name}


def _build_default_hd_ticket_template_payload() -> dict:
    values = escape_template_context(
        {
            "subject_text": "Yeu cau ho tro: {{ doc.name | e }}",
            "description_text": (
                "<p>Xin chao {{ doc.raised_by | e }},</p>"
                "<p>Yeu cau cua ban da duoc ghi nhan voi ma <strong>{{ doc.name | e }}</strong>.</p>"
                "<p>Mo ta: {{ doc.description | e }}</p>"
            ),
        }
    )

    return {
        "template_name": HDTICKET_TEMPLATE_DOCNAME,
        "subject": values["subject_text"],
        "response": values["description_text"],
        "description": values["description_text"],
    }


def ensure_helpdesk_phone_scripts():
    """Install/refresh Helpdesk scripts for phone normalization and contact sync."""
    if not frappe.db.exists("DocType", "HD Ticket"):
        return

    if frappe.db.exists("DocType", "Client Script"):
        _upsert_client_script()
    if frappe.db.exists("DocType", "Server Script"):
        _upsert_server_script()


def _upsert_client_script():
    script = _build_client_script_code()
    doc = _get_or_new_named_doc("Client Script", HDTICKET_PHONE_CLIENT_SCRIPT_NAME)

    values = {
        "dt": "HD Ticket",
        "enabled": 1,
        "script": script,
    }

    if _has_meta_field("Client Script", "view"):
        values["view"] = "Form"

    doc.update(values)
    _save_named_doc(doc)


def _upsert_server_script():
    script = _build_server_script_code()
    doc = _get_or_new_named_doc("Server Script", HDTICKET_PHONE_SERVER_SCRIPT_NAME)

    values = {
        "script_type": "DocType Event",
        "reference_doctype": "HD Ticket",
        "doctype_event": "Before Insert",
        "enabled": 1,
        "script": script,
    }

    doc.update(values)
    _save_named_doc(doc)


def _get_or_new_named_doc(doctype: str, docname: str):
    if frappe.db.exists(doctype, docname):
        return frappe.get_doc(doctype, docname)

    doc = frappe.new_doc(doctype)
    doc.name = docname
    return doc


def _save_named_doc(doc):
    doc.flags.ignore_permissions = True
    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)


def _has_meta_field(doctype: str, fieldname: str) -> bool:
    return bool(frappe.get_meta(doctype).has_field(fieldname))


def _build_client_script_code() -> str:
    return """
const HARAVAN_PHONE_FIELDS = ['phone', 'contact_phone', 'custom_phone', 'phone_number', 'mobile_no'];

function normalizeHaravanPhone(rawValue) {
    if (!rawValue) return '';

    let digits = String(rawValue).replace(/\\D+/g, '');
    if (!digits) return '';

    // +84xxxxxxxxx or 84xxxxxxxxx -> 0xxxxxxxxx
    if (digits.startsWith('84')) {
        digits = '0' + digits.slice(2);
    }

    // collapse leading zeros to a single 0 for VN style numbers
    digits = digits.replace(/^0+/, '0');
    return digits;
}

function getHaravanPhoneField(frm) {
    for (const fieldname of HARAVAN_PHONE_FIELDS) {
        if (Object.prototype.hasOwnProperty.call(frm.doc, fieldname)) {
            return fieldname;
        }
    }
    return null;
}

function setNormalizedPhone(frm) {
    const phoneField = getHaravanPhoneField(frm);
    if (!phoneField) return '';

    const normalized = normalizeHaravanPhone(frm.doc[phoneField] || '');
    if (normalized && normalized !== frm.doc[phoneField]) {
        frm.set_value(phoneField, normalized);
    }
    return normalized || frm.doc[phoneField] || '';
}

function validateHaravanPhone(frm) {
    const phoneField = getHaravanPhoneField(frm);
    if (!phoneField) return;

    const normalized = setNormalizedPhone(frm);
    if (!normalized) return;

    if (!/^0\\d{9,10}$/.test(normalized)) {
        frappe.throw(__('So dien thoai khong hop le. Chi cho phep 10-11 so va phai bat dau bang 0.'));
    }
}

function getPreferredContactPhone(contactDoc) {
    if (!contactDoc) return '';
    if (contactDoc.mobile_no) return normalizeHaravanPhone(contactDoc.mobile_no);
    if (contactDoc.phone) return normalizeHaravanPhone(contactDoc.phone);

    const phoneNos = Array.isArray(contactDoc.phone_nos) ? contactDoc.phone_nos : [];
    for (const row of phoneNos) {
        if (row && row.phone) return normalizeHaravanPhone(row.phone);
    }
    return '';
}

function autofillPhoneFromContact(frm) {
    const phoneField = getHaravanPhoneField(frm);
    if (!phoneField || !frm.doc.contact) return;

    frappe.db.get_doc('Contact', frm.doc.contact).then((contactDoc) => {
        const phone = getPreferredContactPhone(contactDoc);
        if (phone && !frm.doc[phoneField]) {
            frm.set_value(phoneField, phone);
        }
    }).catch(() => {});
}

frappe.ui.form.on('HD Ticket', {
    setup(frm) {
        setNormalizedPhone(frm);
    },
    contact(frm) {
        autofillPhoneFromContact(frm);
    },
    validate(frm) {
        validateHaravanPhone(frm);
    },
    phone(frm) {
        setNormalizedPhone(frm);
    },
    contact_phone(frm) {
        setNormalizedPhone(frm);
    },
    custom_phone(frm) {
        setNormalizedPhone(frm);
    },
    phone_number(frm) {
        setNormalizedPhone(frm);
    },
    mobile_no(frm) {
        setNormalizedPhone(frm);
    }
});
""".strip()


def _build_server_script_code() -> str:
    return """
import re

PHONE_FIELDS = ('phone', 'contact_phone', 'custom_phone', 'phone_number', 'mobile_no')


def _normalize_phone(raw_value):
    if not raw_value:
        return ''

    digits = re.sub(r'\\D+', '', str(raw_value))
    if not digits:
        return ''

    if digits.startswith('84'):
        digits = '0' + digits[2:]

    digits = re.sub(r'^0+', '0', digits)
    return digits


def _get_phone_field_and_value(doc):
    for fieldname in PHONE_FIELDS:
        if doc.meta.has_field(fieldname):
            value = doc.get(fieldname)
            if value:
                return fieldname, value
    return None, ''


def _has_phone_on_contact(contact_doc):
    values = []
    if contact_doc.get('mobile_no'):
        values.append(contact_doc.get('mobile_no'))
    if contact_doc.get('phone'):
        values.append(contact_doc.get('phone'))

    for row in contact_doc.get('phone_nos') or []:
        if row.get('phone'):
            values.append(row.get('phone'))

    normalized_values = {_normalize_phone(v) for v in values if v}
    return any(bool(v) for v in normalized_values)


def _append_phone_to_contact(contact_doc, normalized_phone):
    existing = {_normalize_phone(contact_doc.get('mobile_no') or ''), _normalize_phone(contact_doc.get('phone') or '')}
    for row in contact_doc.get('phone_nos') or []:
        existing.add(_normalize_phone(row.get('phone') or ''))

    if normalized_phone in existing:
        return

    if contact_doc.meta.has_field('phone_nos'):
        contact_doc.append('phone_nos', {'phone': normalized_phone, 'is_primary_phone': 1})
    elif contact_doc.meta.has_field('mobile_no') and not contact_doc.get('mobile_no'):
        contact_doc.set('mobile_no', normalized_phone)
    elif contact_doc.meta.has_field('phone') and not contact_doc.get('phone'):
        contact_doc.set('phone', normalized_phone)

    contact_doc.flags.ignore_permissions = True
    contact_doc.save(ignore_permissions=True)


phone_field, phone_value = _get_phone_field_and_value(doc)
if phone_field:
    normalized_phone = _normalize_phone(phone_value)
    if normalized_phone:
        if not re.match(r'^0\\d{9,10}$', normalized_phone):
            frappe.throw('So dien thoai khong hop le. Chi cho phep 10-11 so va phai bat dau bang 0.')

        doc.set(phone_field, normalized_phone)

        if doc.get('contact') and frappe.db.exists('Contact', doc.get('contact')):
            contact_doc = frappe.get_doc('Contact', doc.get('contact'))
            if not _has_phone_on_contact(contact_doc):
                _append_phone_to_contact(contact_doc, normalized_phone)
""".strip()
