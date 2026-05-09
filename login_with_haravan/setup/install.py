import json

import frappe
from frappe import _

from login_with_haravan.setup.template_safety import escape_template_context

PROVIDER_DOCNAME = "haravan_account"
PROVIDER_NAME = "Haravan Account"
HARAVAN_SOCIAL_ICON_URL = "https://haravandesk.s.frappe.cloud/files/haravan_favicon_24.png"
HDTICKET_PHONE_CLIENT_SCRIPT_NAME = "Haravan HD Ticket Phone Client Script"
HDTICKET_PHONE_SERVER_SCRIPT_NAME = "Haravan HD Ticket Phone Server Script"
HDTICKET_TEMPLATE_DOCTYPE = "HD Ticket Template"
HDTICKET_TEMPLATE_DOCNAME = "Default"


def after_install():
    configure_haravan_social_login()
    _warn_helpdesk_auto_provision_deprecated("after_install")
    ensure_default_hd_ticket_template()


def after_migrate():
    configure_haravan_social_login()
    _warn_helpdesk_auto_provision_deprecated("after_migrate")
    ensure_default_hd_ticket_template()


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
            "icon": HARAVAN_SOCIAL_ICON_URL,
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
    credentials = frappe.conf.get("haravan_login") or {}
    if isinstance(credentials, str):
        try:
            credentials = json.loads(credentials)
        except json.JSONDecodeError:
            credentials = {}

    return {
        "client_id": credentials.get("client_id") or frappe.conf.get("haravan_client_id"),
        "client_secret": credentials.get("client_secret") or frappe.conf.get("haravan_client_secret"),
    }


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
