## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2025-05-13 - Broken Access Control via Overly Permissive Query Conditions
**Vulnerability:** A monkey-patched `get_permission_query_conditions` for the `User` DocType returned an empty string for all users. This effectively bypassed all read permissions, allowing any authenticated user to query and access all other users' records in the system.
**Learning:** In the Frappe framework, returning an empty string `""` in a permission query condition is treated as an unrestricted pass (no SQL filters applied). While this is sometimes done lazily to avoid SQL join syntax errors (like `1054 Unknown column 'tabUser.name'`), it introduces a critical Broken Access Control vulnerability.
**Prevention:** When overriding permission query conditions to solve technical issues, always ensure that non-privileged users are securely restricted to their own records. Never return an empty string unless the user is an 'Administrator' or has the 'System Manager' role. Always sanitize dynamic input using `frappe.db.escape()` to prevent SQL injection.
