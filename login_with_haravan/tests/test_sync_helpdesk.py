"""Unit tests for login_with_haravan.engines.sync_helpdesk."""

import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

# --- Frappe mock setup (shared with other test modules) ---
frappe_mock = sys.modules.get("frappe")
if frappe_mock is None or not isinstance(frappe_mock, MagicMock):
    frappe_mock = MagicMock()
    frappe_mock.DuplicateEntryError = type("DuplicateEntryError", (Exception,), {})
    frappe_mock.utils.now_datetime.return_value = "2026-04-29 12:00:00"
    sys.modules["frappe"] = frappe_mock
    sys.modules["frappe.utils"] = frappe_mock.utils


def _reset_frappe_mock():
    """Fully reset frappe_mock to clean state for each test."""
    frappe_mock.reset_mock()
    frappe_mock.db.exists.side_effect = None
    frappe_mock.db.exists.return_value = None
    frappe_mock.db.get_value.side_effect = None
    frappe_mock.db.get_value.return_value = None
    frappe_mock.new_doc.side_effect = None
    frappe_mock.new_doc.return_value = MagicMock()
    frappe_mock.get_doc.side_effect = None
    frappe_mock.get_doc.return_value = MagicMock()
    frappe_mock.get_all.side_effect = None
    frappe_mock.get_all.return_value = []
    frappe_mock.form_dict = {}

from login_with_haravan.engines.sync_helpdesk import (
    HD_CUSTOMER_LINK_ROLES,
    _make_hd_customer_name,
    _safe_int,
    auto_set_customer,
    enrich_helpdesk_data,
    get_contact_phone_options,
    normalize_phone_key,
    persist_ticket_contact_phone,
    update_user_profile,
    upsert_hd_customer,
    upsert_contact,
    validate_portal_ticket_customer_or_store_url,
)


class TestMakeHdCustomerName(unittest.TestCase):
    """Test the deterministic naming: '[OrgName] - [OrgID]'."""

    def test_basic_format(self):
        self.assertEqual(
            _make_hd_customer_name("12345", "Minh Hải Store"),
            "Minh Hải Store - 12345",
        )

    def test_numeric_orgid(self):
        self.assertEqual(
            _make_hd_customer_name("999", "Test Shop"),
            "Test Shop - 999",
        )

    def test_int_orgid(self):
        self.assertEqual(
            _make_hd_customer_name(12345, "Minh Hải Store"),
            "Minh Hải Store - 12345",
        )


class TestSafeInt(unittest.TestCase):
    """Test _safe_int conversion."""

    def test_string_to_int(self):
        self.assertEqual(_safe_int("12345"), 12345)

    def test_int_passthrough(self):
        self.assertEqual(_safe_int(12345), 12345)

    def test_none_returns_none(self):
        self.assertIsNone(_safe_int(None))

    def test_invalid_returns_none(self):
        self.assertIsNone(_safe_int("abc"))

    def test_float_to_int(self):
        self.assertEqual(_safe_int(12345.0), 12345)


class TestUpdateUserProfile(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    def test_updates_middle_name_when_empty(self):
        """Should set middle_name on User if currently empty."""
        frappe_mock.db.exists.return_value = True
        user_doc = MagicMock()
        user_doc.middle_name = ""
        user_doc.language = "vi"
        frappe_mock.get_doc.return_value = user_doc

        update_user_profile("test@example.com", {"middle_name": "Văn", "locale": ""})

        self.assertEqual(user_doc.middle_name, "Văn")
        user_doc.save.assert_called_once()

    def test_does_not_overwrite_existing_middle_name(self):
        """Should NOT overwrite middle_name if already set."""
        frappe_mock.db.exists.return_value = True
        user_doc = MagicMock()
        user_doc.middle_name = "Existing"
        user_doc.language = "en"
        frappe_mock.get_doc.return_value = user_doc

        update_user_profile("test@example.com", {"middle_name": "New", "locale": "vi"})

        self.assertEqual(user_doc.middle_name, "Existing")
        user_doc.save.assert_not_called()

    def test_sets_language_from_locale(self):
        """Should set language from Haravan locale if empty."""
        frappe_mock.db.exists.return_value = True
        user_doc = MagicMock()
        user_doc.middle_name = "Has"
        user_doc.language = ""
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
        _reset_frappe_mock()

    def test_creates_new_hd_customer_with_orgid_suffix(self):
        """Should create HD Customer with name format '[OrgName] - [OrgID]'."""
        # custom_haravan_orgid lookup returns None, name lookup returns None
        frappe_mock.db.get_value.side_effect = [None, None]
        doc = MagicMock()
        doc.name = "Minh Hải Store - 12345"
        frappe_mock.new_doc.return_value = doc

        result = upsert_hd_customer({"orgid": "12345", "orgname": "Minh Hải Store"})

        frappe_mock.new_doc.assert_called_with("HD Customer")
        self.assertEqual(doc.customer_name, "Minh Hải Store - 12345")
        self.assertEqual(doc.domain, "12345.myharavan.com")
        self.assertEqual(doc.custom_haravan_orgid, 12345)
        self.assertEqual(doc.custom_myharavan, "12345.myharavan.com")
        doc.insert.assert_called_once()
        self.assertEqual(result, "Minh Hải Store - 12345")

    def test_returns_existing_by_orgid_lookup(self):
        """Should find existing HD Customer by custom_haravan_orgid (primary lookup)."""
        # Primary lookup returns name
        frappe_mock.db.get_value.return_value = "Minh Hải Store - 12345"
        frappe_mock.get_doc.return_value = MagicMock(
            domain="12345.myharavan.com",
            custom_haravan_orgid=12345,
            custom_myharavan="12345.myharavan.com",
        )

        result = upsert_hd_customer({"orgid": "12345", "orgname": "Minh Hải Store"})

        self.assertEqual(result, "Minh Hải Store - 12345")
        frappe_mock.new_doc.assert_not_called()

    def test_returns_existing_by_name_fallback(self):
        """Should find existing HD Customer by candidate_name if orgid lookup misses."""
        # custom_haravan_orgid lookup returns None, name lookup returns match
        frappe_mock.db.get_value.side_effect = [None, "Minh Hải Store - 12345"]
        frappe_mock.get_doc.return_value = MagicMock(
            domain="12345.myharavan.com",
            custom_haravan_orgid=12345,
            custom_myharavan="12345.myharavan.com",
        )

        result = upsert_hd_customer({"orgid": "12345", "orgname": "Minh Hải Store"})

        self.assertEqual(result, "Minh Hải Store - 12345")
        frappe_mock.new_doc.assert_not_called()

    def test_returns_none_for_missing_orgid(self):
        """Should return None if orgid is missing."""
        result = upsert_hd_customer({"orgname": "No OrgID Store"})
        self.assertIsNone(result)

    def test_returns_none_for_missing_orgname(self):
        """Should return None if orgname is missing."""
        result = upsert_hd_customer({"orgid": "12345"})
        self.assertIsNone(result)

    def test_orgid_stored_as_int(self):
        """Should convert orgid string to int for custom_haravan_orgid field."""
        frappe_mock.db.get_value.side_effect = [None, None]
        doc = MagicMock()
        doc.name = "Test - 99999"
        frappe_mock.new_doc.return_value = doc

        upsert_hd_customer({"orgid": "99999", "orgname": "Test"})

        self.assertEqual(doc.custom_haravan_orgid, 99999)
        self.assertIsInstance(doc.custom_haravan_orgid, int)

    def test_ignores_legacy_haravan_org_data_on_create(self):
        """Login sync should not write old Haravan commerce enrichment fields."""
        frappe_mock.db.get_value.side_effect = [None, None]
        doc = MagicMock()
        doc.name = "Test Shop - 12345"
        frappe_mock.new_doc.return_value = doc

        normalized = {
            "orgid": "12345",
            "orgname": "Test Shop",
            "haravan_org_data": {
                "plan_display_name": "OMNICHANNEL",
                "plan_status": "active",
                "plan_expired_at": "2027-04-20T16:23:51Z",
                "province_name": "Hồ Chí Minh",
                "country_name": "Vietnam",
            },
        }
        result = upsert_hd_customer(normalized)

        self.assertNotEqual(doc.custom_shopplan_name, "OMNICHANNEL")
        self.assertNotEqual(doc.custom_shopplan_status, "active")
        self.assertNotEqual(doc.custom_province_name, "Hồ Chí Minh")
        self.assertNotEqual(doc.custom_country, "Vietnam")
        doc.insert.assert_called_once()

    def test_creates_hd_customer_without_org_data(self):
        """Should create HD Customer gracefully when haravan_org_data is empty."""
        frappe_mock.db.get_value.side_effect = [None, None]
        doc = MagicMock()
        doc.name = "Test Shop - 12345"
        frappe_mock.new_doc.return_value = doc

        result = upsert_hd_customer({"orgid": "12345", "orgname": "Test Shop"})

        doc.insert.assert_called_once()
        self.assertEqual(result, "Test Shop - 12345")

    def test_does_not_update_legacy_plan_fields_on_existing_customer(self):
        """Bitrix on-demand profile replaced Haravan shop/subscription updates."""
        frappe_mock.db.get_value.return_value = "Test Shop - 12345"
        existing_doc = MagicMock()
        existing_doc.domain = "12345.myharavan.com"
        existing_doc.custom_haravan_orgid = 12345
        existing_doc.custom_myharavan = "12345.myharavan.com"
        existing_doc.custom_shopplan_name = "STANDARD"
        existing_doc.custom_shopplan_status = "active"
        existing_doc.custom_expired_date = "2026-01-01 00:00:00"
        existing_doc.custom_province_name = "Hồ Chí Minh"
        existing_doc.custom_country = "Vietnam"
        existing_doc.custom_first_paid_date = "2025-01-01 00:00:00"
        frappe_mock.get_doc.return_value = existing_doc

        normalized = {
            "orgid": "12345",
            "orgname": "Test Shop",
            "haravan_org_data": {
                "plan_display_name": "OMNICHANNEL",
                "plan_status": "active",
                "plan_expired_at": "2028-01-01T00:00:00Z",
                "province_name": "Hồ Chí Minh",
                "country_name": "Vietnam",
            },
        }
        upsert_hd_customer(normalized)

        self.assertEqual(existing_doc.custom_shopplan_name, "STANDARD")
        existing_doc.save.assert_not_called()


class TestUpsertContact(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    def test_creates_contact_with_hd_customer_link(self):
        """Should create Contact and link to HD Customer."""
        frappe_mock.db.get_value.return_value = None  # Contact not found
        contact_doc = MagicMock()
        frappe_mock.new_doc.return_value = contact_doc

        upsert_contact(
            {"email": "test@example.com", "name": "Test User", "middle_name": ""},
            "Minh Hải Store - 12345",
        )

        frappe_mock.new_doc.assert_called_with("Contact")
        contact_doc.append.assert_called_once_with(
            "links",
            {"link_doctype": "HD Customer", "link_name": "Minh Hải Store - 12345"},
        )
        contact_doc.insert.assert_called_once()

    def test_adds_new_hd_customer_link_to_existing_contact(self):
        """Should add HD Customer link if not already present (multi-org)."""
        frappe_mock.db.get_value.return_value = "existing-contact-001"
        contact_doc = MagicMock()
        contact_doc.links = [
            MagicMock(link_doctype="HD Customer", link_name="Old Store - 11111"),
        ]
        contact_doc.middle_name = "Has"
        frappe_mock.get_doc.return_value = contact_doc

        upsert_contact(
            {"email": "test@example.com", "name": "Test", "middle_name": ""},
            "New Store - 22222",
        )

        contact_doc.append.assert_called_once_with(
            "links",
            {"link_doctype": "HD Customer", "link_name": "New Store - 22222"},
        )
        contact_doc.save.assert_called_once()

    def test_skips_duplicate_hd_customer_link(self):
        """Should NOT add duplicate HD Customer link."""
        frappe_mock.db.get_value.return_value = "existing-contact-001"
        contact_doc = MagicMock()
        contact_doc.links = [
            MagicMock(link_doctype="HD Customer", link_name="Same Store - 12345"),
        ]
        contact_doc.middle_name = "Has"
        frappe_mock.get_doc.return_value = contact_doc

        upsert_contact(
            {"email": "test@example.com", "name": "Test", "middle_name": ""},
            "Same Store - 12345",
        )

        contact_doc.append.assert_not_called()
        contact_doc.save.assert_not_called()

    def test_skips_when_no_email(self):
        """Should skip when email is missing."""
        upsert_contact({"name": "No Email"}, "Store - 12345")
        frappe_mock.db.get_value.assert_not_called()


class TestRoleBasedLinking(unittest.TestCase):
    """Test role-based Contact → HD Customer linking via enrich_helpdesk_data."""

    def setUp(self):
        _reset_frappe_mock()

    def test_hd_customer_link_roles_constant(self):
        """Sanity check: owner and admin are in the link-eligible roles."""
        self.assertIn("owner", HD_CUSTOMER_LINK_ROLES)
        self.assertIn("admin", HD_CUSTOMER_LINK_ROLES)
        self.assertNotIn("staff", HD_CUSTOMER_LINK_ROLES)

    @patch("login_with_haravan.engines.sync_helpdesk.upsert_contact")
    @patch("login_with_haravan.engines.sync_helpdesk.upsert_hd_customer")
    @patch("login_with_haravan.engines.sync_helpdesk.update_user_profile")
    @patch("login_with_haravan.engines.haravan_identity.normalize_haravan_profile")
    def test_owner_gets_hd_customer_link(self, mock_normalize, mock_update, mock_upsert_cust, mock_upsert_contact):
        """Owner role → Contact linked to HD Customer."""
        mock_normalize.return_value = {
            "email": "owner@shop.com", "orgid": "123", "orgname": "Shop",
            "role": ["owner"],
        }
        mock_upsert_cust.return_value = "Shop - 123"

        enrich_helpdesk_data("owner@shop.com", {})

        mock_upsert_contact.assert_called_once()
        args = mock_upsert_contact.call_args
        self.assertEqual(args[0][1], "Shop - 123")  # hd_customer_name passed

    @patch("login_with_haravan.engines.sync_helpdesk.upsert_contact")
    @patch("login_with_haravan.engines.sync_helpdesk.upsert_hd_customer")
    @patch("login_with_haravan.engines.sync_helpdesk.update_user_profile")
    @patch("login_with_haravan.engines.haravan_identity.normalize_haravan_profile")
    def test_admin_gets_hd_customer_link(self, mock_normalize, mock_update, mock_upsert_cust, mock_upsert_contact):
        """Admin role → Contact linked to HD Customer."""
        mock_normalize.return_value = {
            "email": "admin@shop.com", "orgid": "123", "orgname": "Shop",
            "role": ["admin"],
        }
        mock_upsert_cust.return_value = "Shop - 123"

        enrich_helpdesk_data("admin@shop.com", {})

        mock_upsert_contact.assert_called_once()
        args = mock_upsert_contact.call_args
        self.assertEqual(args[0][1], "Shop - 123")

    @patch("login_with_haravan.engines.sync_helpdesk.upsert_contact")
    @patch("login_with_haravan.engines.sync_helpdesk.upsert_hd_customer")
    @patch("login_with_haravan.engines.sync_helpdesk.update_user_profile")
    @patch("login_with_haravan.engines.haravan_identity.normalize_haravan_profile")
    def test_staff_does_not_get_hd_customer_link(self, mock_normalize, mock_update, mock_upsert_cust, mock_upsert_contact):
        """Staff role → Contact NOT linked to HD Customer (sees only own tickets)."""
        mock_normalize.return_value = {
            "email": "staff@shop.com", "orgid": "123", "orgname": "Shop",
            "role": ["staff"],
        }
        mock_upsert_cust.return_value = "Shop - 123"

        enrich_helpdesk_data("staff@shop.com", {})

        mock_upsert_contact.assert_called_once()
        args = mock_upsert_contact.call_args
        self.assertIsNone(args[0][1])  # hd_customer_name is None

    @patch("login_with_haravan.engines.sync_helpdesk.upsert_contact")
    @patch("login_with_haravan.engines.sync_helpdesk.upsert_hd_customer")
    @patch("login_with_haravan.engines.sync_helpdesk.update_user_profile")
    @patch("login_with_haravan.engines.haravan_identity.normalize_haravan_profile")
    def test_empty_role_does_not_get_link(self, mock_normalize, mock_update, mock_upsert_cust, mock_upsert_contact):
        """Empty role → Contact NOT linked to HD Customer."""
        mock_normalize.return_value = {
            "email": "norole@shop.com", "orgid": "123", "orgname": "Shop",
            "role": [],
        }
        mock_upsert_cust.return_value = "Shop - 123"

        enrich_helpdesk_data("norole@shop.com", {})

        args = mock_upsert_contact.call_args
        self.assertIsNone(args[0][1])


class TestAutoSetCustomer(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    def test_auto_sets_single_customer(self):
        """Should auto-set customer when user has exactly 1 HD Customer."""
        frappe_mock.session.user = "test@example.com"
        frappe_mock.get_all.return_value = [
            MagicMock(hd_customer="Minh Hải Store - 12345"),
        ]
        doc = MagicMock()
        doc.customer = None

        auto_set_customer(doc)

        self.assertEqual(doc.customer, "Minh Hải Store - 12345")

    def test_does_not_set_when_multiple_customers(self):
        """Should NOT set customer when user has multiple HD Customers."""
        frappe_mock.session.user = "test@example.com"
        frappe_mock.get_all.return_value = [
            MagicMock(hd_customer="Store A - 11111"),
            MagicMock(hd_customer="Store B - 22222"),
        ]
        doc = MagicMock()
        doc.customer = None

        auto_set_customer(doc)

        self.assertIsNone(doc.customer)

    def test_preserves_existing_customer(self):
        """Should NOT override if customer is already set."""
        frappe_mock.session.user = "test@example.com"
        doc = MagicMock()
        doc.customer = "Existing Customer"

        auto_set_customer(doc)

        self.assertEqual(doc.customer, "Existing Customer")
        frappe_mock.get_all.assert_not_called()

    def test_skips_for_guest(self):
        """Should skip for Guest users."""
        frappe_mock.session.user = "Guest"
        doc = MagicMock()
        doc.customer = None

        auto_set_customer(doc)

        self.assertIsNone(doc.customer)
        frappe_mock.get_all.assert_not_called()

    def test_portal_ticket_requires_customer_or_store_url(self):
        """Should block portal tickets without customer context."""
        frappe_mock.throw.side_effect = Exception("missing customer context")
        doc = SimpleNamespace(
            via_customer_portal=1,
            customer="",
            custom_store_url="",
        )

        with self.assertRaises(Exception) as context:
            validate_portal_ticket_customer_or_store_url(doc)

        self.assertIn("missing customer context", str(context.exception))
        frappe_mock.throw.assert_called_once_with(
            "Vui lòng chọn Customer hoặc nhập Link Web / MyHaravan trước khi tạo ticket.",
            title="Thiếu thông tin khách hàng",
        )

    def test_portal_ticket_uses_submitted_values_before_backend_autofill(self):
        """Should block when the submitted portal form omitted both context fields."""
        frappe_mock.throw.side_effect = Exception("missing submitted customer context")
        frappe_mock.form_dict = {
            "doc": {
                "customer": "",
                "custom_store_url": "",
            }
        }
        doc = SimpleNamespace(
            via_customer_portal=1,
            customer="Backend Auto-filled Customer",
            custom_store_url="",
        )

        with self.assertRaises(Exception) as context:
            validate_portal_ticket_customer_or_store_url(doc)

        self.assertIn("missing submitted customer context", str(context.exception))

    def test_portal_ticket_allows_customer_without_store_url(self):
        """Should allow portal tickets when a customer is selected."""
        doc = SimpleNamespace(
            via_customer_portal=1,
            customer="Trang trí phòng xinh - 1000008079",
            custom_store_url="",
        )

        validate_portal_ticket_customer_or_store_url(doc)

        frappe_mock.throw.assert_not_called()

    def test_portal_ticket_allows_store_url_without_customer(self):
        """Should allow portal tickets when a store URL is provided."""
        doc = SimpleNamespace(
            via_customer_portal=1,
            customer="",
            custom_store_url="shop.myharavan.com",
        )

        validate_portal_ticket_customer_or_store_url(doc)

        frappe_mock.throw.assert_not_called()


class TestContactPhoneSuggestions(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    def test_mobile_no_is_first(self):
        frappe_mock.get_doc.return_value = MagicMock(
            mobile_no="0938411165",
            phone="028123456",
        )

        self.assertEqual(get_contact_phone_options("contact-1"), ["0938411165", "028123456"])

    def test_falls_back_to_phone_when_mobile_no_is_empty(self):
        frappe_mock.get_doc.return_value = MagicMock(
            mobile_no="",
            phone="0900000001",
        )

        self.assertEqual(get_contact_phone_options("contact-1"), ["0900000001"])

    def test_normalize_phone_key_matches_vietnam_country_code(self):
        self.assertEqual(normalize_phone_key("+84 938 411 165"), "0938411165")


class TestPersistTicketContactPhone(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    def test_sets_new_ticket_phone_on_contact_main_fields(self):
        contact = MagicMock()
        contact.mobile_no = ""
        contact.phone = ""
        frappe_mock.get_doc.return_value = contact
        doc = SimpleNamespace(custom_phone="0938411165", contact="contact-1", raised_by="")

        persist_ticket_contact_phone(doc)

        self.assertEqual(contact.mobile_no, "0938411165")
        self.assertEqual(contact.phone, "0938411165")
        contact.append.assert_not_called()
        contact.save.assert_called_once_with(ignore_permissions=True)

    def test_does_not_duplicate_existing_phone_with_different_format(self):
        contact = MagicMock()
        contact.mobile_no = "+84 938 411 165"
        contact.phone = ""
        frappe_mock.get_doc.return_value = contact
        doc = SimpleNamespace(custom_phone="0938411165", contact="contact-1", raised_by="")

        persist_ticket_contact_phone(doc)

        contact.save.assert_not_called()

    def test_falls_back_to_raised_by_contact(self):
        frappe_mock.db.get_value.return_value = "contact-from-email"
        contact = MagicMock()
        contact.mobile_no = ""
        contact.phone = "028123456"
        frappe_mock.get_doc.return_value = contact
        doc = SimpleNamespace(custom_phone="0938411165", contact="", raised_by="owner@example.com")

        persist_ticket_contact_phone(doc)

        frappe_mock.db.get_value.assert_called_with("Contact", {"email_id": "owner@example.com"}, "name")
        self.assertEqual(contact.mobile_no, "0938411165")
        self.assertEqual(contact.phone, "028123456")
        contact.save.assert_called_once_with(ignore_permissions=True)


class TestLegacyHaravanCommerceDataIgnored(unittest.TestCase):
    """Haravan login no longer writes commerce metadata during login."""

    def setUp(self):
        _reset_frappe_mock()

    def test_create_ignores_shop_created_at(self):
        """Should not use shop.created_at for first paid date."""
        frappe_mock.db.get_value.side_effect = [None, None]
        doc = MagicMock()
        doc.name = "Test Shop - 12345"
        frappe_mock.new_doc.return_value = doc

        normalized = {
            "orgid": "12345",
            "orgname": "Test Shop",
            "haravan_org_data": {
                "plan_display_name": "AFFILIATE",
                "created_at": "2020-04-20T17:07:15.58Z",
                # no subscription_created_at
            },
        }
        upsert_hd_customer(normalized)

        self.assertNotIsInstance(doc.custom_first_paid_date, str)

    def test_create_ignores_subscription_created_at(self):
        """Should not use subscription_created_at for first paid date."""
        frappe_mock.db.get_value.side_effect = [None, None]
        doc = MagicMock()
        doc.name = "Test Shop - 12345"
        frappe_mock.new_doc.return_value = doc

        normalized = {
            "orgid": "12345",
            "orgname": "Test Shop",
            "haravan_org_data": {
                "subscription_created_at": "2021-06-15T10:00:00Z",
                "created_at": "2020-04-20T17:07:15.58Z",
            },
        }
        upsert_hd_customer(normalized)

        self.assertNotIsInstance(doc.custom_first_paid_date, str)


if __name__ == "__main__":
    unittest.main()
