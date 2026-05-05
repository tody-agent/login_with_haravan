## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2026-05-05 - Missing Document-Level Authorization on User-Input Lookups (IDOR)
**Vulnerability:** In `login_with_haravan/engines/customer_enrichment.py`, the function `refresh_customer_profile` called `frappe.get_doc()` with document IDs derived from user input but did not verify document-level access permissions first.
**Learning:** In the Frappe framework, `frappe.get_doc()` does not enforce document-level permissions by default when called from Python code. Without an explicit check, this creates an Insecure Direct Object Reference (IDOR) vulnerability where users can fetch and view documents they do not own or have permission to see.
**Prevention:** Always call `frappe.has_permission(doctype, 'read', docname, throw=True)` explicitly before fetching documents based on user input in API endpoints or background logic triggered by users.
