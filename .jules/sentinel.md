## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.
## 2024-05-12 - Secure Permission Query Patching
**Vulnerability:** A monkey-patch on `User.get_permission_query_conditions` returned an empty string for all users to bypass a SQL join bug. This disabled row-level security for the entire User doctype, exposing all users' data.
**Learning:** Overriding permission queries to fix framework bugs can inadvertently strip away critical security barriers if applied universally. Furthermore, manually re-implementing conditions like `tabUser.name = {user_name}` requires `frappe.db.escape()` to avoid SQL injection.
**Prevention:** When patching permissions, apply the most restrictive condition possible by default (e.g. self-only access using escaped values) and only grant bypasses to specifically authorized roles like System Manager.
