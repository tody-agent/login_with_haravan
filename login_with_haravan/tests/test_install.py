"""Unit tests for login_with_haravan.setup.install — custom field provisioning."""

import sys
import unittest
from unittest.mock import MagicMock

# --- Frappe mock setup (shared with other test modules) ---
frappe_mock = sys.modules.get("frappe")
if frappe_mock is None:
    frappe_mock = MagicMock()
    frappe_mock.DuplicateEntryError = type("DuplicateEntryError", (Exception,), {})
    sys.modules["frappe"] = frappe_mock
    sys.modules.setdefault("frappe.utils", frappe_mock.utils)

from login_with_haravan.setup.install import (
    HD_CUSTOMER_CUSTOM_FIELDS,
    ensure_hd_customer_custom_fields,
)


class TestEnsureHdCustomerCustomFields(unittest.TestCase):
    def setUp(self):
        frappe_mock.reset_mock()
        # Reset side_effect to avoid leaking across tests
        frappe_mock.db.exists.side_effect = None
        frappe_mock.db.exists.return_value = None
        frappe_mock.new_doc.side_effect = None
        frappe_mock.new_doc.return_value = MagicMock()

    def tearDown(self):
        # Clean up side_effect so other test modules aren't affected
        frappe_mock.db.exists.side_effect = None
        frappe_mock.db.exists.return_value = None
        frappe_mock.new_doc.side_effect = None
        frappe_mock.db.get_value.side_effect = None
        frappe_mock.db.get_value.return_value = None

    def test_skips_when_helpdesk_not_installed(self):
        """Should exit early if HD Customer DocType doesn't exist."""
        frappe_mock.db.exists.return_value = False

        ensure_hd_customer_custom_fields()

        # Only one exists check (for DocType), no custom field creation
        frappe_mock.db.exists.assert_called_once_with("DocType", "HD Customer")
        frappe_mock.new_doc.assert_not_called()

    def test_skips_when_custom_field_already_exists(self):
        """Should not create a Custom Field that already exists."""
        # First call: DocType check → True, Second: Custom Field check → True
        frappe_mock.db.exists.side_effect = [True, True]

        ensure_hd_customer_custom_fields()

        frappe_mock.new_doc.assert_not_called()

    def test_creates_haravan_orgid_custom_field(self):
        """Should create haravan_orgid Custom Field on HD Customer."""
        # DocType exists, Custom Field does not exist
        frappe_mock.db.exists.side_effect = [True, False]
        cf_doc = MagicMock()
        frappe_mock.new_doc.return_value = cf_doc

        ensure_hd_customer_custom_fields()

        frappe_mock.new_doc.assert_called_once_with("Custom Field")
        self.assertEqual(cf_doc.dt, "HD Customer")
        self.assertEqual(cf_doc.fieldname, "haravan_orgid")
        self.assertEqual(cf_doc.fieldtype, "Data")
        self.assertEqual(cf_doc.label, "Haravan Org ID")
        cf_doc.insert.assert_called_once()
        frappe_mock.db.commit.assert_called_once()
        frappe_mock.clear_cache.assert_called_once_with(doctype="HD Customer")

    def test_handles_duplicate_entry_gracefully(self):
        """Should not crash on DuplicateEntryError (race condition)."""
        frappe_mock.db.exists.side_effect = [True, False]
        cf_doc = MagicMock()
        cf_doc.insert.side_effect = frappe_mock.DuplicateEntryError()
        frappe_mock.new_doc.return_value = cf_doc

        # Should not raise
        ensure_hd_customer_custom_fields()

        frappe_mock.db.commit.assert_called_once()

    def test_custom_fields_definition_has_haravan_orgid(self):
        """Verify the custom fields definition is correct."""
        self.assertEqual(len(HD_CUSTOMER_CUSTOM_FIELDS), 1)
        field = HD_CUSTOMER_CUSTOM_FIELDS[0]
        self.assertEqual(field["fieldname"], "haravan_orgid")
        self.assertEqual(field["fieldtype"], "Data")
        self.assertEqual(field["unique"], 1)
        self.assertEqual(field["insert_after"], "domain")


if __name__ == "__main__":
    unittest.main()
