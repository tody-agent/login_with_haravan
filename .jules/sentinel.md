## 2025-05-01 - Missing Authorization Checks on API Endpoints
**Vulnerability:** Setup and configuration functions in `login_with_haravan/setup/install.py` were exposed to the public API using `@frappe.whitelist()`, but lacked role-based access control.
**Learning:** In the Frappe framework, `@frappe.whitelist()` exposes functions to the API, allowing any authenticated user to potentially trigger them. It does not enforce role checks automatically.
**Prevention:** Always add explicit authorization checks, such as `frappe.only_for("System Manager")` or `frappe.has_permission(...)`, inside whitelisted functions that perform sensitive operations like modifying system configuration or metadata.

## 2025-05-01 - Missing Document-Level Permission Checks on Read Endpoints
**Vulnerability:** The `refresh_customer_profile` API endpoint in `login_with_haravan/customer_profile.py` exposed sensitive customer profile information (from Bitrix and local documents) based on `hd_customer` and `contact` IDs provided by the user. While the function was whitelisted for API access using `@frappe.whitelist()`, it lacked explicit document-level permission checks before fetching and returning the data, leading to an Insecure Direct Object Reference (IDOR) vulnerability.
**Learning:** In the Frappe framework, `frappe.get_doc()` does not enforce read permissions by default when called from backend Python scripts (it skips permission checks to allow internal logic to run). If user input is passed to an endpoint that reads a document, the framework does not automatically verify the user has access.
**Prevention:** Always use `frappe.has_permission(doctype, 'read', docname, throw=True)` inside whitelisted functions before accessing or returning document data based on user-supplied IDs.
