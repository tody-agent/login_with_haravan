"""Regression tests for Customer Profile sync patch snippets."""

import unittest

from scripts import patch_profile_sync_company_id as patch


class ProfileSyncCompanyIdPatchTest(unittest.TestCase):
    def test_form_script_passes_matched_company_id_to_sync_api(self):
        source = f"before\n          {patch.FORM_OLD}\nafter"

        patched, changed = patch.patch_once(source, patch.FORM_OLD, patch.FORM_NEW, "form")

        self.assertTrue(changed)
        self.assertIn("const syncCompanyId = company.company_id || orgId || \"\";", patched)
        self.assertIn("company_id: syncCompanyId", patched)

    def test_sync_api_accepts_company_id_from_request_before_ticket_fields(self):
        source = f"before\n            {patch.SERVER_OLD}\nafter"

        patched, changed = patch.patch_once(source, patch.SERVER_OLD, patch.SERVER_NEW, "server")

        self.assertTrue(changed)
        self.assertIn('frappe.form_dict.get("company_id")', patched)
        self.assertLess(
            patched.index('frappe.form_dict.get("company_id")'),
            patched.index('ticket.get("custom_haravan_profile_orgid")'),
        )

    def test_patch_is_idempotent_when_new_snippet_already_exists(self):
        patched, changed = patch.patch_once(patch.FORM_NEW, patch.FORM_OLD, patch.FORM_NEW, "form")

        self.assertFalse(changed)
        self.assertEqual(patched, patch.FORM_NEW)


if __name__ == "__main__":
    unittest.main()
