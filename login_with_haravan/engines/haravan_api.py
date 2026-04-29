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

def fetch_org_and_subscription_data(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    data = {
        "plan_name": None,
        "plan_display_name": None,
        "plan_status": None,
        "plan_expired_at": None,
        "province_name": None,
        "country_name": None,
        "shop_owner": None,
        "created_at": None,
        "email": None,
        "domain": None,
        "myharavan_domain": None,
        "name": None,
        "subscription_status": None,
        "subscription_created_at": None,
        "subscription_expired_at": None,
        "subscription_cancelled_at": None,
        "app_activated": False,
        "amount_paid": 0,
    }

    try:
        # 1) Lấy thông tin shop
        shop_resp = requests.get(
            "https://apis.haravan.com/com/shop.json",
            headers=headers,
            timeout=10
        )
        if shop_resp.status_code == 200:
            shop = shop_resp.json().get("shop", {})
            data["plan_name"] = shop.get("plan_name")
            data["plan_display_name"] = shop.get("plan_display_name")
            data["plan_status"] = shop.get("plan_status")
            data["plan_expired_at"] = shop.get("plan_expired_at")
            data["province_name"] = shop.get("province_name")
            data["country_name"] = shop.get("country_name")
            data["shop_owner"] = shop.get("shop_owner")
            data["created_at"] = shop.get("created_at")
            data["email"] = shop.get("email")
            data["domain"] = shop.get("domain")
            data["myharavan_domain"] = shop.get("myharavan_domain")
            data["name"] = shop.get("name")
    except Exception as e:
        frappe.log_error(f"Failed to fetch Haravan shop info: {e}", "Haravan API Error")

    try:
        # 2) Lấy subscription (trạng thái thanh toán app)
        sub_resp = requests.get(
            "https://apis.haravan.com/com/apps/app_subscriptions.json",
            headers=headers,
            timeout=10
        )
        if sub_resp.status_code == 200:
            subscriptions = sub_resp.json().get("app_subscriptions", [])

            # Tìm active subscription
            active_sub = None
            for sub in subscriptions:
                if sub.get("status") == "active":
                    expired_at = sub.get("expired_at")
                    if expired_at:
                        # Simple check or full timezone check
                        active_sub = sub
                        break

            # Or just take the first one if we want to store latest status
            if active_sub:
                data["subscription_status"] = active_sub.get("status")
                data["subscription_created_at"] = active_sub.get("created_at")
                data["subscription_expired_at"] = active_sub.get("expired_at")
                data["subscription_cancelled_at"] = active_sub.get("cancelled_at")
                data["amount_paid"] = active_sub.get("amount_paid")
                data["app_activated"] = True
            elif subscriptions:
                # Store the latest cancelled/expired sub if no active one
                latest = subscriptions[0]
                data["subscription_status"] = latest.get("status")
                data["subscription_created_at"] = latest.get("created_at")
                data["subscription_expired_at"] = latest.get("expired_at")
                data["subscription_cancelled_at"] = latest.get("cancelled_at")



    except Exception as e:
        frappe.log_error(f"Failed to fetch Haravan app subscriptions: {e}", "Haravan API Error")

    return data
