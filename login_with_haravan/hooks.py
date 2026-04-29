app_name = "login_with_haravan"
app_title = "Login With Haravan"
app_version = "0.1.1"
app_publisher = "Haravan"
app_description = "Social login bridge from Haravan Account to Frappe Helpdesk"
app_email = "dev@haravan.com"
app_license = "MIT"

after_install = "login_with_haravan.setup.install.after_install"
after_migrate = "login_with_haravan.setup.install.after_migrate"

web_include_js = [
    "/assets/login_with_haravan/js/haravan_login_redirect.js",
    "/assets/login_with_haravan/js/haravan_org_selector.js",
]

doc_events = {
    "HD Ticket": {
        "before_insert": "login_with_haravan.engines.sync_helpdesk.auto_set_customer"
    }
}
