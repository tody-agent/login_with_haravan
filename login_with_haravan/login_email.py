"""Haravan-specific login link email."""

from html import escape

import frappe
from frappe.rate_limiter import rate_limit
from frappe.www.login import _generate_temporary_login_link, get_login_with_email_link_ratelimit


LOGIN_EMAIL_SUBJECT = "Đăng nhập vào Haravan"


def _login_email_message(link: str, minutes: int) -> str:
    safe_link = escape(link, quote=True)
    return f"""
<div style="background-color: #f4f4f4; padding: 48px 24px;">
  <div style="background-color: #ffffff; border-radius: 8px; margin: 0 auto; max-width: 640px; padding: 48px 32px; text-align: center;">
    <div style="font-size: 24px; font-weight: 700; line-height: 1.35; margin-bottom: 8px;">
      Nhấn vào nút bên dưới để đăng nhập vào Haravan
    </div>
    <div style="font-size: 16px; line-height: 1.5; margin-bottom: 24px;">
      Liên kết sẽ hết hạn sau {minutes} phút
    </div>
    <div style="border-top: 1px solid #e8e8e8; margin: 0 auto 24px; max-width: 420px;"></div>
    <div style="font-size: 20px; font-weight: 700; line-height: 1.35; margin-bottom: 8px;">
      Click on the button to log in to Haravan
    </div>
    <div style="font-size: 15px; line-height: 1.5; margin-bottom: 28px;">
      The link will expire in {minutes} minutes
    </div>
    <a href="{safe_link}" style="background-color: #171717; border-radius: 6px; color: #ffffff; display: inline-block; font-size: 16px; font-weight: 600; line-height: 1.35; padding: 13px 28px; text-decoration: none;">
      Đăng nhập vào Haravan<br>
      <span style="font-size: 14px; font-weight: 500;">Log In To Haravan</span>
    </a>
  </div>
</div>
"""


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=get_login_with_email_link_ratelimit, seconds=60 * 60)
def send_login_link(email: str):
    """Send Haravan's bilingual login link email."""
    if not frappe.get_system_settings("login_with_email_link"):
        return

    expiry = frappe.get_system_settings("login_with_email_link_expiry") or 10
    link = _generate_temporary_login_link(email, expiry)

    frappe.sendmail(
        subject=LOGIN_EMAIL_SUBJECT,
        recipients=email,
        message=_login_email_message(link=link, minutes=expiry),
        now=True,
    )
