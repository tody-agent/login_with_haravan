"""Regression tests for the Desk-managed Profile - Ticket Routing Server Script."""

import re
import unittest
from pathlib import Path

from scripts import deploy_profile_ticket_routing as deploy


class ProfileTicketRoutingServerScriptTest(unittest.TestCase):
    def test_server_script_is_compile_safe_doctype_event(self):
        compile(deploy.SERVER_SCRIPT, "<server-script>", "exec")
        compile(deploy.ASSIGNMENT_SERVER_SCRIPT, "<assignment-server-script>", "exec")

        self.assertEqual(deploy.SERVER_SCRIPT_NAME, "Profile - Ticket Routing")
        self.assertEqual(
            deploy.ASSIGNMENT_SERVER_SCRIPT_NAME,
            "Profile - Ticket Round Robin Assignment",
        )
        self.assertEqual(deploy.REFERENCE_DOCTYPE, "HD Ticket")
        self.assertEqual(deploy.DOCTYPE_EVENT, "Before Insert")
        self.assertEqual(deploy.ASSIGNMENT_DOCTYPE_EVENT, "After Insert")

    def test_server_script_uses_hd_customer_segment_and_shopplan(self):
        self.assertIn('"HD Customer"', deploy.SERVER_SCRIPT)
        self.assertIn('"custom_customer_segment"', deploy.SERVER_SCRIPT)
        self.assertIn('"custom_shopplan_name"', deploy.SERVER_SCRIPT)
        self.assertIn('doc.get("agent_group")', deploy.SERVER_SCRIPT)
        self.assertIn("Manual/API agent_group already set", deploy.SERVER_SCRIPT)
        self.assertNotIn("crm.company.list.json", deploy.SERVER_SCRIPT)

    def test_server_script_contains_medium_sme_rules_and_teams(self):
        self.assertIn('"grow" in shopplan_key', deploy.SERVER_SCRIPT)
        self.assertIn('"scale" in shopplan_key', deploy.SERVER_SCRIPT)
        self.assertIn('MEDIUM_SCALE_TEAM = "Medium - Scale"', deploy.SERVER_SCRIPT)
        self.assertIn('MEDIUM_GROW_TEAM = "Medium - Grow"', deploy.SERVER_SCRIPT)
        self.assertIn('DEFAULT_TEAM = "CS 60p"', deploy.SERVER_SCRIPT)
        self.assertIn('routing_reason_prefix = "Auto-routed:"', deploy.SERVER_SCRIPT)

    def test_server_script_guards_against_loops_and_manual_overrides(self):
        self.assertIn("if not current_agent_group:", deploy.SERVER_SCRIPT)
        self.assertIn("doc.agent_group = target_team", deploy.SERVER_SCRIPT)
        self.assertNotIn("AUTO_ROUTED_AGENT_GROUPS", deploy.SERVER_SCRIPT)
        self.assertNotIn("frappe.db.set_value", deploy.SERVER_SCRIPT)

    def test_deploy_script_uses_single_spec_list_and_json_summary_log(self):
        self.assertEqual(len(deploy.SERVER_SCRIPT_SPECS), 2)
        self.assertEqual(
            [spec["name"] for spec in deploy.SERVER_SCRIPT_SPECS],
            [deploy.SERVER_SCRIPT_NAME, deploy.ASSIGNMENT_SERVER_SCRIPT_NAME],
        )
        source = Path(deploy.__file__).read_text(encoding="utf-8")
        self.assertIn('"status": "success"', source)
        self.assertIn('"deployed": deployed', source)
        self.assertIn('"backup_dir": str(backup_dir)', source)

    def test_assignment_script_only_assigns_auto_routed_tickets(self):
        self.assertIn('"Medium - Scale"', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn('"Medium - Grow"', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn('"CS 60p"', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn('routing_reason.startswith("Auto-routed:")', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn('"reference_type": "HD Ticket"', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn('"status": "Open"', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn('"description": assignment_description', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn('order_by="creation desc"', deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertNotIn("frappe.cache", deploy.ASSIGNMENT_SERVER_SCRIPT)
        self.assertIn("frappe.desk.form.assign_to.add", deploy.ASSIGNMENT_SERVER_SCRIPT)

    def test_server_script_has_no_runtime_app_dependency_or_legacy_google_api(self):
        for script in (deploy.SERVER_SCRIPT, deploy.ASSIGNMENT_SERVER_SCRIPT):
            self.assertNotIn("login_with_haravan", script)
            self.assertIsNone(re.search(r"^\s*(from|import)\s+", script, flags=re.MULTILINE))
            self.assertNotIn("def ", script)
            self.assertNotIn("script.googleusercontent.com", script)
            self.assertNotIn("Google Apps Script", script)


if __name__ == "__main__":
    unittest.main()
