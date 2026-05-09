## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2026-05-06 - Insecure Direct Object Reference (IDOR) via `frappe.get_doc()`
**Vulnerability:** The API endpoints `get_ticket_customer_profile` and `get_ticket_bitrix_profile` fetched linked documents (`HD Customer`, `Contact`) using `frappe.get_doc()` based on context linked to user input, but without enforcing read permissions for those specific linked documents.
**Learning:** `frappe.get_doc()` bypasses document-level authorization natively when called in Python. If user input (or values derived from user input) is used to look up related documents, an IDOR vulnerability can occur if `frappe.has_permission` is not explicitly checked.
**Prevention:** Always precede `frappe.get_doc(doctype, docname)` with `frappe.has_permission(doctype, "read", docname, throw=True)` when the document to be fetched may be outside the user's explicit permission scope, particularly in whitelisted functions.
