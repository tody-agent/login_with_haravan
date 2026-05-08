## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2025-05-08 - IDOR due to empty query permissions
**Vulnerability:** The User `get_permission_query_conditions` monkey patch in `login_with_haravan/hooks.py` returned an empty string for all users, entirely bypassing row-level access control on the User DocType and creating an IDOR vulnerability where any authenticated user could query any other user.
**Learning:** In the Frappe framework, `get_permission_query_conditions` restricts what records a user can access when a list is fetched. Returning an empty string `""` tells Frappe "no restrictions apply", which allows access to all records.
**Prevention:** When monkey-patching `get_permission_query_conditions` (e.g., to resolve 1054 SQL join errors by omitting the hardcoded `tabUser.name`), restrict normal users to their own record (e.g. `return f"tabUser.name = '{user_name}'"`) and only return `""` for privileged users like "Administrator" or "System Manager".
