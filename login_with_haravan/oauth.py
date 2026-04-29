import json

import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.utils.oauth import get_info_via_oauth, login_oauth_user
from frappe.www.login import sanitize_redirect

from login_with_haravan.engines.oauth_payload import decode_json_payload
from login_with_haravan.engines.oauth_state import decode_oauth_state, encode_oauth_state
from login_with_haravan.engines.haravan_identity import (
    build_link_fields,
    make_link_name,
    normalize_haravan_profile,
)

PROVIDER = "haravan_account"
REDIRECT_COOKIE = "haravan_login_redirect_to"


def decoder_compat(value):
    return decode_json_payload(value)


def _log_oauth_failure(stage: str, exc: Exception, context: dict | None = None):
    safe_context = {"stage": stage, "exception": f"{type(exc).__name__}: {exc}"}
    if context:
        safe_context.update(context)

    frappe.log_error(
        "\n\n".join(
            [
                json.dumps(safe_context, ensure_ascii=False, sort_keys=True, default=str),
                frappe.get_traceback(),
            ]
        ),
        "Haravan social login failed",
    )


def _with_redirect_override(state: str) -> str:
    redirect_to = _get_redirect_override()
    if not redirect_to:
        return state

    decoded_state = decode_oauth_state(state)
    decoded_state["redirect_to"] = redirect_to
    _clear_redirect_cookie()
    return encode_oauth_state(decoded_state)


def _get_redirect_override() -> str | None:
    request = getattr(frappe.local, "request", None)
    if not request:
        return None

    redirect_to = request.args.get("redirect-to") or request.cookies.get(REDIRECT_COOKIE)
    if not redirect_to:
        return None

    sanitized = sanitize_redirect(redirect_to)
    if not sanitized:
        return None

    if sanitized.endswith("/login") or "/login?" in sanitized:
        return None

    return sanitized


def _clear_redirect_cookie():
    cookie_manager = getattr(frappe.local, "cookie_manager", None)
    if cookie_manager:
        cookie_manager.delete_cookie(REDIRECT_COOKIE)


@frappe.whitelist(allow_guest=True)
def login_via_haravan(code: str | None = None, state: str | None = None, **kwargs):
    if not code or not state:
        frappe.throw(_("Missing OAuth code or state from Haravan."))

    state = _with_redirect_override(state)

    try:
        info = get_info_via_oauth(PROVIDER, code, decoder=decoder_compat)
    except Exception as exc:
        _log_oauth_failure(
            "get_info_via_oauth",
            exc,
            {
                "has_code": bool(code),
                "has_state": bool(state),
                "scope": kwargs.get("scope"),
                "session_state_present": bool(kwargs.get("session_state")),
            },
        )
        raise

    try:
        profile = normalize_haravan_profile(info)
    except Exception as exc:
        _log_oauth_failure(
            "normalize_haravan_profile",
            exc,
            {
                "userinfo_keys": sorted(info.keys()) if isinstance(info, dict) else [],
                "has_email": bool(isinstance(info, dict) and info.get("email")),
                "has_sub": bool(isinstance(info, dict) and info.get("sub")),
                "has_orgid": bool(isinstance(info, dict) and (info.get("orgid") or info.get("org_id"))),
            },
        )
        raise

    try:
        login_oauth_user(profile, provider=PROVIDER, state=state)
        _persist_after_login(profile)
    except Exception as exc:
        _log_oauth_failure(
            "login_oauth_user",
            exc,
            {
                "profile_keys": sorted(profile.keys()) if isinstance(profile, dict) else [],
                "email": profile.get("email") if isinstance(profile, dict) else None,
                "has_sub": bool(isinstance(profile, dict) and profile.get("sub")),
                "has_orgid": bool(isinstance(profile, dict) and profile.get("orgid")),
            },
        )
        raise


def _persist_after_login(profile: dict):
    user = getattr(frappe.session, "user", None)
    if not user or user == "Guest":
        return

    try:
        upsert_haravan_account_link(user, profile)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Haravan Account Link persistence failed")


def upsert_haravan_account_link(user: str, profile: dict):
    fields = build_link_fields(user, profile)
    doc_name = make_link_name(fields["haravan_orgid"], fields["haravan_userid"])
    fields["last_login"] = now_datetime()

    if frappe.db.exists("Haravan Account Link", doc_name):
        doc = frappe.get_doc("Haravan Account Link", doc_name)
        doc.update(fields)
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.new_doc("Haravan Account Link")
        doc.name = doc_name
        doc.update(fields)
        doc.flags.ignore_permissions = True
        doc.insert(ignore_permissions=True)

    return doc.name
