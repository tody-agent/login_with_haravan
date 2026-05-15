## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2025-05-15 - Authorization Bypass via get_permission_query_conditions Patch
**Vulnerability:** The `get_permission_query_conditions` hook in `login_with_haravan/hooks.py` was monkey-patched to unconditionally return an empty string (`""`) for all users. This completely bypassed row-level security for the `User` DocType, allowing unprivileged users to read other users' sensitive data.
**Learning:** In the Frappe framework, returning an empty string from `get_permission_query_conditions` bypasses all permission checks. When monkey-patching this method (e.g., to fix SQL join errors caused by hardcoded table names), you must not unintentionally grant wide access.
**Prevention:** Always explicitly restrict access for non-privileged users when overriding permission queries. Use `frappe.db.escape(user_name)` to build secure SQL conditions (like `` f"`tabUser`.name = {safe_user}" ``) and restrict the empty string bypass to specific privileged roles like `Administrator` or `System Manager`.
