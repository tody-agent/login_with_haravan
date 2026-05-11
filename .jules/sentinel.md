## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2025-05-01 - Permission Query Condition Bypass in Hooks
**Vulnerability:** A monkey-patch for `get_permission_query_conditions` in `hooks.py` returned an empty string for all users to prevent an SQL join error. This bypassed row-level security for the `User` DocType, creating an IDOR vulnerability where any user could read all `User` records.
**Learning:** Returning an empty string from a `get_permission_query_conditions` hook completely disables read-access controls for that DocType for the current user. When trying to resolve SQL join issues (like "Unknown column 'tabUser.name'"), it is insecure to disable permissions globally.
**Prevention:** When monkey-patching or implementing `get_permission_query_conditions`, only return an empty string for privileged roles like 'Administrator' or 'System Manager'. For non-privileged users, always return a restrictive condition that limits them to their own records (e.g., `` `tabUser`.name = '{user_name}' ``).
