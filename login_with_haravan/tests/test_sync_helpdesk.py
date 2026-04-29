"""Unit tests for login_with_haravan.engines.sync_helpdesk."""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# --- Frappe mock setup (same pattern as existing tests) ---
frappe_mock = MagicMock()
frappe_mock.DuplicateEntryError = type("DuplicateEntryError", (Exception,), {})
frappe_mock.utils.now_datetime.return_value = "2026-04-29 12:00:00"
sys.modules.setdefault("frappe", frappe_mock)
sys.modules.setdefault("frappe.utils", frappe_mock.utils)

from login_with_haravan.engines.sync_helpdesk import (
    auto_set_customer,
    enrich_helpdesk_data,
    update_user_profile,
    upsert_hd_customer,
    upsert_contact,
)


class TestUpdateUserProfile(unittest.TestCase):
    def setUp(self):
        frappe_mock.reset_mock()

    def test_updates_middle_name_when_empty(self):
        """Should set middle_name on User if currently empty."""
        user_doc = MagicMock()
        user_doc.middle_name = ""
        user_doc.language = "vi"
        frappe_mock.db.exists.return_value = True
        frappe_mock.get_doc.return_value = user_doc

        update_user_profile("test@example.com", {"middle_name": "Văn", "locale": ""})

        self.assertEqual(user_doc.middle_name, "Văn")
        user_doc.save.assert_called_once()

    def test_does_not_overwrite_existing_middle_name(self):
        """Should NOT overwrite middle_name if already set."""
        user_doc = MagicMock()
        user_doc.middle_name = "Existing"
        user_doc.language = "en"
        frappe_mock.db.exists.return_value = True
        frappe_mock.get_doc.return_value = user_doc

        update_user_profile("test@example.com", {"middle_name": "New", "locale": ""})

        self.assertEqual(user_doc.middle_name, "Existing")
        user_doc.save.assert_not_called()

    def test_sets_language_from_locale(self):
        """Should set language from Haravan locale if empty."""
        user_doc = MagicMock()
        user_doc.middle_name = "Existing"
        user_doc.language = ""
        frappe_mock.db.exists.return_value = True
        frappe_mock.get_doc.return_value = user_doc

        update_user_profile("test@example.com", {"middle_name": "", "locale": "vi"})

        self.assertEqual(user_doc.language, "vi")
        user_doc.save.assert_called_once()

    def test_skips_nonexistent_user(self):
        """Should gracefully skip if User doc doesn't exist."""
        frappe_mock.db.exists.return_value = False

        update_user_profile("ghost@example.com", {"middle_name": "Test", "locale": "en"})

        frappe_mock.get_doc.assert_not_called()


class TestUpsertHdCustomer(unittest.TestCase):
    def setUp(self):
        frappe_mock.reset_mock()

    def test_creates_new_hd_customer(self):
        """Should create HD Customer when name doesn't exist."""
        frappe_mock.db.get_value.return_value = None
        new_doc = MagicMock()
        new_doc.name = "Minh Hải Store"
        frappe_mock.new_doc.return_value = new_doc

        result = upsert_hd_customer({
            "orgid": "12345",
            "orgname": "Minh Hải Store",
            "orgcat": "retail",
        })

        frappe_mock.new_doc.assert_called_with("HD Customer")
        new_doc.insert.assert_called_once()
        self.assertEqual(result, "Minh Hải Store")

    def test_returns_existing_hd_customer(self):
        """Should return existing HD Customer name when it already exists."""
        frappe_mock.db.get_value.side_effect = [
            "Minh Hải Store",  # First call: lookup by customer_name
        ]
        existing_doc = MagicMock()
        existing_doc.domain = "12345.myharavan.com"
        existing_doc.haravan_orgid = "12345"
        existing_doc.haravan_orgcat = "retail"
        frappe_mock.get_doc.return_value = existing_doc

        result = upsert_hd_customer({
            "orgid": "12345",
            "orgname": "Minh Hải Store",
            "orgcat": "retail",
        })

        self.assertEqual(result, "Minh Hải Store")
        frappe_mock.new_doc.assert_not_called()

    def test_returns_none_for_missing_orgid(self):
        """Should return None if orgid is missing."""
        result = upsert_hd_customer({"orgname": "Test"})
        self.assertIsNone(result)

    def test_returns_none_for_missing_orgname(self):
        """Should return None if orgname is missing."""
        result = upsert_hd_customer({"orgid": "123"})
        self.assertIsNone(result)


class TestUpsertContact(unittest.TestCase):
    def setUp(self):
        frappe_mock.reset_mock()

    def test_creates_contact_with_hd_customer_link(self):
        """Should create Contact and link to HD Customer."""
        frappe_mock.db.get_value.return_value = None
        contact_doc = MagicMock()
        contact_doc.links = []
        frappe_mock.new_doc.return_value = contact_doc

        upsert_contact(
            {"email": "user@example.com", "name": "Test User", "middle_name": ""},
            "Minh Hải Store",
        )

        frappe_mock.new_doc.assert_called_with("Contact")
        contact_doc.insert.assert_called_once()
        contact_doc.append.assert_called_once_with(
            "links",
            {"link_doctype": "HD Customer", "link_name": "Minh Hải Store"},
        )

    def test_adds_new_hd_customer_link_to_existing_contact(self):
        """Should add HD Customer link if not already present (multi-org)."""
        frappe_mock.db.get_value.return_value = "CONTACT-001"
        contact_doc = MagicMock()
        # Existing links — has one org but not the new one
        existing_link = MagicMock()
        existing_link.link_doctype = "HD Customer"
        existing_link.link_name = "Old Store"
        contact_doc.links = [existing_link]
        contact_doc.middle_name = "Existing"
        frappe_mock.get_doc.return_value = contact_doc

        upsert_contact(
            {"email": "user@example.com", "name": "Test User", "middle_name": ""},
            "New Store",
        )

        contact_doc.append.assert_called_once_with(
            "links",
            {"link_doctype": "HD Customer", "link_name": "New Store"},
        )
        contact_doc.save.assert_called_once()

    def test_skips_duplicate_hd_customer_link(self):
        """Should NOT add duplicate HD Customer link."""
        frappe_mock.db.get_value.return_value = "CONTACT-001"
        contact_doc = MagicMock()
        existing_link = MagicMock()
        existing_link.link_doctype = "HD Customer"
        existing_link.link_name = "Minh Hải Store"
        contact_doc.links = [existing_link]
        contact_doc.middle_name = "Existing"
        frappe_mock.get_doc.return_value = contact_doc

        upsert_contact(
            {"email": "user@example.com", "name": "Test", "middle_name": ""},
            "Minh Hải Store",
        )

        contact_doc.append.assert_not_called()
        contact_doc.save.assert_not_called()

    def test_skips_when_no_email(self):
        """Should skip when email is missing."""
        upsert_contact({"name": "Test"}, "Minh Hải Store")
        frappe_mock.db.get_value.assert_not_called()


class TestAutoSetCustomer(unittest.TestCase):
    def setUp(self):
        frappe_mock.reset_mock()

    def test_auto_sets_single_customer(self):
        """Should auto-set customer when user has exactly 1 HD Customer."""
        doc = MagicMock()
        doc.customer = None
        frappe_mock.session.user = "user@example.com"

        link_row = MagicMock()
        link_row.hd_customer = "Minh Hải Store"
        frappe_mock.get_all.return_value = [link_row]

        auto_set_customer(doc)

        self.assertEqual(doc.customer, "Minh Hải Store")

    def test_does_not_set_when_multiple_customers(self):
        """Should NOT set customer when user has multiple HD Customers."""
        doc = MagicMock()
        doc.customer = None
        frappe_mock.session.user = "user@example.com"

        link1 = MagicMock()
        link1.hd_customer = "Store A"
        link2 = MagicMock()
        link2.hd_customer = "Store B"
        frappe_mock.get_all.return_value = [link1, link2]

        auto_set_customer(doc)

        self.assertIsNone(doc.customer)

    def test_preserves_existing_customer(self):
        """Should NOT override if customer is already set."""
        doc = MagicMock()
        doc.customer = "Already Set"

        auto_set_customer(doc)

        self.assertEqual(doc.customer, "Already Set")
        frappe_mock.get_all.assert_not_called()

    def test_skips_for_guest(self):
        """Should skip for Guest users."""
        doc = MagicMock()
        doc.customer = None
        frappe_mock.session.user = "Guest"

        auto_set_customer(doc)

        frappe_mock.get_all.assert_not_called()


if __name__ == "__main__":
    unittest.main()
