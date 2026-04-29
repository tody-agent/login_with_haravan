import requests
import frappe
from frappe.utils import get_url

from login_with_haravan.engines.site_config import get_haravan_login_credentials


def fetch_haravan_info_and_token(code: str, decoder=None, conf=None) -> tuple[dict, str]:
    provider_doc = frappe.get_doc("Social Login Key", "haravan_account")
    credentials = get_haravan_login_credentials(conf=conf, provider_doc=provider_doc)
    client_id = credentials.get("client_id")
    client_secret = credentials.get("client_secret")
    if not client_id or not client_secret:
        frappe.throw("Haravan OAuth client credentials are not configured in site config.")

    redirect_uri = get_url(provider_doc.redirect_url)

    base_url = provider_doc.base_url
    token_url = provider_doc.access_token_url
    if not token_url.startswith("http"):
        token_url = f"{base_url}{token_url}"

    userinfo_url = provider_doc.api_endpoint
    if not userinfo_url.startswith("http"):
        userinfo_url = f"{base_url}{userinfo_url}"

    # 1. Exchange code for token
    token_resp = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code
        },
        timeout=15
    )
    token_resp.raise_for_status()
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        frappe.throw("Failed to obtain access token from Haravan")

    # 2. Fetch UserInfo
    info_resp = requests.get(
        userinfo_url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15
    )
    info_resp.raise_for_status()
    info = decoder(info_resp.content) if decoder else info_resp.json()

    return info, access_token
