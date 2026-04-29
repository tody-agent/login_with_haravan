import json

import frappe

from login_with_haravan.setup.install import PROVIDER_DOCNAME


@frappe.whitelist()
def get_haravan_login_status():
    if not frappe.has_permission("Social Login Key", "read", PROVIDER_DOCNAME):
        frappe.throw("Not permitted", frappe.PermissionError)

    if not frappe.db.exists("Social Login Key", PROVIDER_DOCNAME):
        return {
            "success": True,
            "data": {"provider_exists": False},
            "message": "Haravan Social Login Key does not exist.",
        }

    doc = frappe.get_doc("Social Login Key", PROVIDER_DOCNAME)
    auth_url_data = doc.auth_url_data or "{}"
    if isinstance(auth_url_data, str):
        try:
            auth_url_data = json.loads(auth_url_data)
        except json.JSONDecodeError:
            auth_url_data = {"_parse_error": True, "raw": doc.auth_url_data}

    existing_secret = doc.get_password("client_secret", raise_exception=False)

    return {
        "success": True,
        "data": {
            "provider_exists": True,
            "enabled": bool(doc.enable_social_login),
            "provider_name": doc.provider_name,
            "base_url": doc.base_url,
            "custom_base_url": bool(doc.custom_base_url),
            "authorize_url": doc.authorize_url,
            "access_token_url": doc.access_token_url,
            "redirect_url": doc.redirect_url,
            "full_redirect_url": frappe.utils.get_url(doc.redirect_url),
            "api_endpoint": doc.api_endpoint,
            "user_id_property": doc.user_id_property,
            "sign_ups": doc.sign_ups,
            "has_client_id": bool(doc.client_id),
            "has_client_secret": bool(existing_secret),
            "auth_url_data": auth_url_data,
        },
        "message": "Haravan Social Login Key status.",
    }
