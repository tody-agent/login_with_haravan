"""Regression tests for the Desk-managed Profile - Ticket Routing Server Script."""

import re
import unittest

from scripts import deploy_profile_ticket_routing as deploy


class ProfileTicketRoutingServerScriptTest(unittest.TestCase):
    def test_server_script_is_compile_safe_doctype_event(self):
        compile(deploy.SERVER_SCRIPT, "<server-script>", "exec")

        self.assertEqual(deploy.SERVER_SCRIPT_NAME, "Profile - Ticket Routing")
        self.assertEqual(deploy.REFERENCE_DOCTYPE, "HD Ticket")
        self.assertEqual(deploy.DOCTYPE_EVENT, "Before Save")

    def test_server_script_uses_customer_first_then_bitrix_fallback(self):
        self.assertIn('"HD Customer"', deploy.SERVER_SCRIPT)
        self.assertIn('"custom_customer_segment"', deploy.SERVER_SCRIPT)
        self.assertIn('doc.get("custom_orgid")', deploy.SERVER_SCRIPT)
        self.assertIn('"UF_CRM_COMPANY_ID"', deploy.SERVER_SCRIPT)
        self.assertIn("crm.company.list.json", deploy.SERVER_SCRIPT)
        self.assertIn('"custom_haravan_profile_orgid"', deploy.SERVER_SCRIPT)

    def test_server_script_contains_medium_sme_rules_and_teams(self):
        self.assertIn('"grow" in current_shopplan_key', deploy.SERVER_SCRIPT)
        self.assertIn('"scale" in current_shopplan_key', deploy.SERVER_SCRIPT)
        self.assertIn('last_hsi_segment == "HSI_500+"', deploy.SERVER_SCRIPT)
        self.assertIn('MEDIUM_TEAM = "Medium"', deploy.SERVER_SCRIPT)
        self.assertIn('SME_TEAM = "CS 60p"', deploy.SERVER_SCRIPT)
        self.assertIn('"After Sales"', deploy.SERVER_SCRIPT)
        self.assertIn('"Service Ecom"', deploy.SERVER_SCRIPT)

    def test_server_script_guards_against_loops_and_manual_overrides(self):
        self.assertIn("AUTO_ROUTED_AGENT_GROUPS", deploy.SERVER_SCRIPT)
        self.assertIn("current_agent_group in AUTO_ROUTED_AGENT_GROUPS", deploy.SERVER_SCRIPT)
        self.assertIn("frappe.db.set_value", deploy.SERVER_SCRIPT)
        self.assertIn("update_modified=False", deploy.SERVER_SCRIPT)
        self.assertIn('profile_org_id == org_id', deploy.SERVER_SCRIPT)

    def test_server_script_has_no_runtime_app_dependency_or_legacy_google_api(self):
        self.assertNotIn("login_with_haravan", deploy.SERVER_SCRIPT)
        self.assertIsNone(re.search(r"^\s*(from|import)\s+", deploy.SERVER_SCRIPT, flags=re.MULTILINE))
        self.assertNotIn("def ", deploy.SERVER_SCRIPT)
        self.assertNotIn("script.googleusercontent.com", deploy.SERVER_SCRIPT)
        self.assertNotIn("Google Apps Script", deploy.SERVER_SCRIPT)


if __name__ == "__main__":
    unittest.main()
