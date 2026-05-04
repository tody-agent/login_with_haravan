## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2025-05-01 - Missing Document-Level Authorization in API Endpoints (IDOR)
**Vulnerability:** The `refresh_customer_profile` API endpoint accepted user-provided document names (`hd_customer` and `contact`) and passed them directly to `frappe.get_doc()` without verifying if the requesting user had read access to those specific documents.
**Learning:** `frappe.get_doc()` does not enforce document-level permissions by default when called from Python code. If its parameters come from user input, this creates an Insecure Direct Object Reference (IDOR) vulnerability.
**Prevention:** Always explicitly call `frappe.has_permission(doctype, 'read', docname, throw=True)` before fetching documents based on user input in API endpoints.
