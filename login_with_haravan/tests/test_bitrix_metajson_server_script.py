"""Regression tests for Desk-managed Bitrix metajson Server Script deployment."""

import unittest
import re

from scripts import deploy_bitrix_metajson_enrichment as deploy


class BitrixMetajsonServerScriptTest(unittest.TestCase):
    def test_server_script_is_source_controlled_safe_exec_api(self):
        compile(deploy.SERVER_SCRIPT, "<server-script>", "exec")

        self.assertEqual(deploy.API_METHOD, "haravan_bitrix_metajson_company_enrichment")
        self.assertIn("frappe.form_dict.get(\"orgid\")", deploy.SERVER_SCRIPT)
        self.assertIn("frappe.make_post_request", deploy.SERVER_SCRIPT)
        self.assertIn("bitrix_refresh_ttl_minutes", deploy.SERVER_SCRIPT)
        self.assertIn("custom_bitrix_last_checked_at", deploy.SERVER_SCRIPT)
        self.assertIn("custom_bitrix_company_modified_at", deploy.SERVER_SCRIPT)
        self.assertIn("frappe.form_dict.get(\"ticket\")", deploy.SERVER_SCRIPT)
        self.assertIn("frappe.db.set_value(\"HD Ticket\"", deploy.SERVER_SCRIPT)
        self.assertIn("HD Customer Data", deploy.SERVER_SCRIPT)
        self.assertIn('customer.customer_name = str(company_title) + " - " + orgid', deploy.SERVER_SCRIPT)

    def test_server_script_does_not_depend_on_custom_app_runtime(self):
        self.assertNotIn("login_with_haravan", deploy.SERVER_SCRIPT)
        self.assertIsNone(re.search(r"^\s*(from|import)\s+", deploy.SERVER_SCRIPT, flags=re.MULTILINE))
        self.assertNotIn("def ", deploy.SERVER_SCRIPT)

    def test_server_script_silently_skips_missing_orgid_and_not_found(self):
        self.assertIn("\"missing_orgid\"", deploy.SERVER_SCRIPT)
        self.assertIn("\"not_found\"", deploy.SERVER_SCRIPT)
        self.assertIn("No Bitrix company found.", deploy.SERVER_SCRIPT)
        self.assertNotIn("No orgid supplied.\")\nfrappe.log_error", deploy.SERVER_SCRIPT)

    def test_deploy_creates_only_guard_custom_fields(self):
        fieldnames = {field["fieldname"] for field in deploy.CUSTOM_FIELDS}
        self.assertEqual(
            fieldnames,
            {
                "custom_bitrix_last_checked_at",
                "custom_bitrix_company_modified_at",
                "custom_bitrix_not_found_at",
            },
        )


if __name__ == "__main__":
    unittest.main()
