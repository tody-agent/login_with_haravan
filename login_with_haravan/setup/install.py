import json

import frappe
from frappe import _

from login_with_haravan.engines.site_config import get_haravan_login_credentials

PROVIDER_DOCNAME = "haravan_account"
PROVIDER_NAME = "Haravan Account"

# HD Customer custom fields are managed manually via Frappe Customize Form.
# Production fields: custom_haravan_orgid (Int), custom_myharavan (Data),
# custom_shopplan_name (Data), custom_customer_segment (Select),
# custom_hsi_segment (Select), custom_first_paid_date (Datetime)


def after_install():
    configure_haravan_social_login()


def after_migrate():
    configure_haravan_social_login()





@frappe.whitelist()
def configure_haravan_social_login(
    client_id: str | None = None,
    client_secret: str | None = None,
    enable: int | str | bool | None = None,
):
    explicit_client_secret = client_secret
    doc = _get_or_create_social_login_key()
    credentials = _get_configured_credentials(doc)
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
            "redirect_url": getattr(doc, "redirect_url", None) or "/api/method/login_with_haravan.oauth.login_via_haravan",
            "api_endpoint": "/connect/userinfo",
            "api_endpoint_args": None,
            "auth_url_data": json.dumps(
                {
                    "response_mode": "query",
                    "response_type": "code",
                    "scope": "openid profile email org userinfo com.read_shop",
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
            "redirect_url": frappe.utils.get_url(doc.redirect_url),
            "credential_source": credentials.get("source"),
            "client_id_source": credentials.get("client_id_source"),
            "client_secret_source": credentials.get("client_secret_source"),
            "client_secret_stored_in_doctype": bool(
                client_secret and not client_secret_from_site_config
            ),
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


def _get_configured_credentials(provider_doc=None) -> dict:
    # Frappe core get_oauth_keys() looks for f"{provider}_login" = "haravan_account_login".
    # The shorter "haravan_login" and flat keys are accepted for backward compatibility.
    return get_haravan_login_credentials(provider_doc=provider_doc)
