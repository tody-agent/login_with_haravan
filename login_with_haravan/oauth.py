import json

import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.utils.oauth import get_info_via_oauth, login_oauth_user

from login_with_haravan.engines.haravan_identity import (
    build_link_fields,
    make_link_name,
    normalize_haravan_profile,
)

PROVIDER = "haravan_account"


def decoder_compat(value):
    return json.loads(bytes(value).decode("utf-8"))


@frappe.whitelist(allow_guest=True)
def login_via_haravan(code: str | None = None, state: str | None = None, **kwargs):
    if not code or not state:
        frappe.throw(_("Missing OAuth code or state from Haravan."))

    try:
        info = get_info_via_oauth(PROVIDER, code, decoder=decoder_compat)
        profile = normalize_haravan_profile(info)
        login_oauth_user(profile, provider=PROVIDER, state=state)
        _persist_after_login(profile)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Haravan social login failed")
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
