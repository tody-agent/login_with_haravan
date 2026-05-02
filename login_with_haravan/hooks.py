app_name = "login_with_haravan"
app_title = "Login With Haravan"
app_version = "0.1.12"
app_publisher = "Tody"
app_description = "Login With Haravan Single Sign On Module"
app_email = "todyle@haravan.com"
app_license = "mit"

after_install = "login_with_haravan.setup.install.after_install"
after_migrate = "login_with_haravan.setup.install.after_migrate"

web_include_js = [
    "/assets/login_with_haravan/js/haravan_login_redirect.js",
    "/assets/login_with_haravan/js/haravan_org_selector.js",
    "/assets/login_with_haravan/js/customer_profile_panel.js",
]

extend_doctype_class = {
    "HD Ticket": "login_with_haravan.overrides.hd_ticket.HDTicketCCMixin",
}

doc_events = {
    "HD Ticket": {
        "before_insert": "login_with_haravan.engines.sync_helpdesk.auto_set_customer",
        "before_validate": "login_with_haravan.engines.ticket_cc.validate_ticket_cc_emails",
        "after_insert": "login_with_haravan.engines.ticket_cc.send_ticket_cc_created_notification",
    }
}

def _patch_frappe_user_permission_query():
    """
    Monkey patch Frappe core's User permission query to avoid the 1054 SQL error
    when querying User fields (like user_image) from a cross-table join (e.g. HD Agent).
    """
    try:
        import frappe
        from frappe.core.doctype.user import user

        if getattr(user.get_permission_query_conditions, "_patched", False):
            return

        def _patched_get_permission_query_conditions(user_name):
            if user_name == "Administrator":
                return ""
            # Returning empty string prevents the hardcoded `tabUser`.name
            # from breaking cross-table joins in frappe.client.get_list.
            return ""

        _patched_get_permission_query_conditions._patched = True
        user.get_permission_query_conditions = _patched_get_permission_query_conditions
    except Exception:
        pass

_patch_frappe_user_permission_query()
