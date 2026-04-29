import json

import frappe
from frappe import _

PROVIDER_DOCNAME = "haravan_account"
PROVIDER_NAME = "Haravan Account"

# Custom fields to inject into HD Customer (belongs to helpdesk app)
HD_CUSTOMER_CUSTOM_FIELDS = [
    {
        "fieldname": "haravan_orgid",
        "fieldtype": "Data",
        "label": "Haravan Org ID",
        "insert_after": "domain",
        "unique": 1,
        "in_list_view": 1,
        "translatable": 0,
    },
]


def after_install():
    configure_haravan_social_login()
    ensure_hd_customer_custom_fields()


def after_migrate():
    configure_haravan_social_login()
    ensure_hd_customer_custom_fields()


def ensure_hd_customer_custom_fields():
    """Create custom fields on HD Customer if they don't exist.

    HD Customer belongs to the helpdesk app. We add haravan_orgid as a
    Custom Field so our sync engine can look up customers by org ID.
    """
    if not frappe.db.exists("DocType", "HD Customer"):
        return  # Helpdesk not installed yet

    for field_def in HD_CUSTOMER_CUSTOM_FIELDS:
        fieldname = field_def["fieldname"]
        cf_name = f"HD Customer-{fieldname}"

        if frappe.db.exists("Custom Field", cf_name):
            continue

        try:
            cf = frappe.new_doc("Custom Field")
            cf.dt = "HD Customer"
            cf.module = "Login With Haravan"
            for key, value in field_def.items():
                setattr(cf, key, value)
            cf.flags.ignore_permissions = True
            cf.insert(ignore_permissions=True)
            frappe.logger("haravan").info(
                f"Created Custom Field '{fieldname}' on HD Customer"
            )
        except frappe.DuplicateEntryError:
            pass  # Already exists — race condition safe
        except Exception as e:
            frappe.log_error(
                f"Failed to create Custom Field '{fieldname}' on HD Customer: {e}",
                "Haravan Install Error",
            )

    frappe.db.commit()
    frappe.clear_cache(doctype="HD Customer")


@frappe.whitelist()
def configure_haravan_social_login(
    client_id: str | None = None,
    client_secret: str | None = None,
    enable: int | str | bool | None = None,
):
    credentials = _get_configured_credentials()
    client_id = client_id or credentials.get("client_id")
    client_secret = client_secret or credentials.get("client_secret")

    doc = _get_or_create_social_login_key()
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
            "redirect_url": "/api/method/login_with_haravan.oauth.login_via_haravan",
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
    if client_secret:
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
            "redirect_url": frappe.utils.get_url(doc.redirect_url),
        },
        "message": "Haravan social login key configured.",
    }


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


def _get_configured_credentials() -> dict:
    # Frappe core get_oauth_keys() looks for f"{provider}_login" = "haravan_account_login"
    # We also support the shorter "haravan_login" for backward compatibility.
    credentials = (
        frappe.conf.get("haravan_account_login")
        or frappe.conf.get("haravan_login")
        or {}
    )
    if isinstance(credentials, str):
        try:
            credentials = json.loads(credentials)
        except json.JSONDecodeError:
            credentials = {}

    return {
        "client_id": credentials.get("client_id") or frappe.conf.get("haravan_client_id"),
        "client_secret": credentials.get("client_secret") or frappe.conf.get("haravan_client_secret"),
    }
