## 2026-05-18 - Authorization Bypass in User Permission Query Condition
**Vulnerability:** The `get_permission_query_conditions` for the `User` DocType was patched to return an empty string for all users to prevent SQL join errors, completely bypassing row-level access controls for the User list.
**Learning:** Returning an empty string in `get_permission_query_conditions` bypasses all permission checks for that DocType. When overriding it to resolve SQL join errors, explicitly check privileges.
**Prevention:** Use `frappe.has_permission(doctype, ptype='read', user=user_name)` to return an empty string for allowed users, and restrict others to their own records securely using `frappe.db.escape(user_name)` with explicit table prefix (e.g., `` `tabUser`.name = {safe_user} ``).

## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.
