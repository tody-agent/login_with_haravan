## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2025-05-01 - Bypassed Role-Based Row-Level Access Controls
**Vulnerability:** The monkeypatched hook `_patched_get_permission_query_conditions` for User DocType in `login_with_haravan/hooks.py` returned an empty string for all users, completely bypassing row-level access permissions.
**Learning:** Returning an empty string from the permission query hook in Frappe effectively grants any user full visibility to all records of that DocType, causing a severe Authorization Bypass vulnerability.
**Prevention:** Only return an empty string for privileged roles like "Administrator" or "System Manager". For standard users, explicitly restrict records to the user context (e.g. `f"name = {frappe.db.escape(user_name)}"`) when patching SQL conditions. Ensure not to break cross-table joins by omitting the table prefix (e.g. `tabUser.`) where appropriate.
