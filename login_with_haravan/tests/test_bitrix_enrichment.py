"""Unit tests for Bitrix on-demand customer enrichment."""

import sys
import unittest
from unittest.mock import MagicMock, patch


frappe_mock = sys.modules.get("frappe")
if frappe_mock is None or not isinstance(frappe_mock, MagicMock):
    frappe_mock = MagicMock()
    sys.modules["frappe"] = frappe_mock
    sys.modules["frappe.utils"] = frappe_mock.utils


def _reset_frappe_mock():
    frappe_mock.reset_mock()
    frappe_mock.db.exists.side_effect = None
    frappe_mock.db.exists.return_value = None
    frappe_mock.db.get_value.side_effect = None
    frappe_mock.db.get_value.return_value = None
    frappe_mock.get_doc.side_effect = None
    frappe_mock.get_doc.return_value = MagicMock()
    frappe_mock.new_doc.side_effect = None
    frappe_mock.new_doc.return_value = MagicMock()
    frappe_mock.get_all.side_effect = None
    frappe_mock.get_all.return_value = []
    frappe_mock.has_permission.return_value = True
    frappe_mock.utils.now_datetime.return_value = "2026-04-29 12:00:00"


class BitrixConfigTest(unittest.TestCase):
    def test_bitrix_runtime_config_is_masked_and_inside_is_removed(self):
        from login_with_haravan.engines.site_config import get_helpdesk_secret_status

        status = get_helpdesk_secret_status(
            conf={
                "inside_api_key": "old-inside-secret",
                "bitrix_webhook_url": "https://example.bitrix24.vn/rest/1/secret/",
                "bitrix_access_token": "bitrix-token",
                "bitrix_enabled": 1,
            }
        )

        self.assertNotIn("inside", status)
        self.assertTrue(status["bitrix"]["bitrix_webhook_url"]["configured"])
        self.assertTrue(status["bitrix"]["bitrix_access_token"]["configured"])
        self.assertNotIn("old-inside-secret", repr(status))
        self.assertNotIn("bitrix-token", repr(status))


class CustomerEnrichmentTest(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    @patch("login_with_haravan.engines.customer_enrichment.get_bitrix_config")
    @patch("login_with_haravan.engines.customer_enrichment.BitrixClient")
    def test_refresh_matches_company_by_domain_before_contact_lookup(self, client_cls, config_mock):
        from login_with_haravan.engines.customer_enrichment import refresh_customer_profile

        config_mock.return_value = {"enabled": True, "configured": True}
        client = client_cls.return_value
        client.find_companies.return_value = [
            {"ID": "42", "TITLE": "Bitrix Company", "WEB": [{"VALUE": "shop.myharavan.com"}]}
        ]
        client.find_contacts.return_value = [
            {"ID": "77", "NAME": "Owner", "EMAIL": [{"VALUE": "owner@example.com"}]}
        ]
        client.build_entity_url.side_effect = lambda entity, entity_id: f"https://bitrix/{entity}/{entity_id}/"

        customer = MagicMock()
        customer.name = "12345 - Shop"
        customer.customer_name = "12345 - Shop"
        customer.domain = "shop.myharavan.com"
        customer.custom_haravan_orgid = 12345
        contact = MagicMock()
        contact.name = "owner@example.com"
        contact.email_id = "owner@example.com"
        contact.phone = ""
        contact.mobile_no = ""
        frappe_mock.get_doc.side_effect = [customer, contact]

        result = refresh_customer_profile("12345 - Shop", "owner@example.com")

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["bitrix"]["company"]["id"], "42")
        self.assertEqual(result["data"]["bitrix"]["contact"]["id"], "77")
        client.find_companies.assert_called_once_with(
            domain="shop.myharavan.com",
            haravan_orgid="12345",
        )
        client.find_contacts.assert_called_once_with(
            email="owner@example.com",
            phone=None,
        )

    @patch("login_with_haravan.engines.customer_enrichment.get_bitrix_config")
    @patch("login_with_haravan.engines.customer_enrichment.BitrixClient")
    def test_profile_open_fetches_bitrix_lazily_not_during_login(self, client_cls, config_mock):
        from login_with_haravan.engines.customer_enrichment import get_ticket_customer_profile

        config_mock.return_value = {"enabled": True, "configured": True}
        client = client_cls.return_value
        client.find_companies.return_value = []
        client.find_contacts.return_value = []
        frappe_mock.db.exists.return_value = True
        frappe_mock.db.get_value.return_value = {
            "customer": "12345 - Shop",
            "contact": "owner@example.com",
            "raised_by": "owner@example.com",
        }

        customer = MagicMock()
        customer.name = "12345 - Shop"
        customer.customer_name = "12345 - Shop"
        customer.domain = "shop.myharavan.com"
        customer.custom_haravan_orgid = 12345
        contact = MagicMock()
        contact.name = "owner@example.com"
        contact.email_id = "owner@example.com"
        contact.phone = ""
        contact.mobile_no = ""
        frappe_mock.get_doc.side_effect = [customer, contact]

        result = get_ticket_customer_profile("HD-1")

        self.assertTrue(result["success"])
        client.find_companies.assert_called_once()

    @patch("login_with_haravan.engines.customer_enrichment.get_bitrix_config")
    @patch("login_with_haravan.engines.customer_enrichment.BitrixClient")
    def test_active_bitrix_responsible_updates_ticket_custom_responsible(self, client_cls, config_mock):
        from login_with_haravan.engines.customer_enrichment import refresh_customer_profile

        config_mock.return_value = {
            "enabled": True,
            "configured": True,
            "responsible_configured": True,
        }
        client = client_cls.return_value
        client.find_companies.return_value = [
            {"ID": "42", "TITLE": "Bitrix Company", "ASSIGNED_BY_ID": "338"}
        ]
        client.find_contacts.return_value = []
        client.get_user.return_value = {
            "ID": "338",
            "ACTIVE": True,
            "EMAIL": "owner@example.com",
            "NAME": "Nguyen",
            "LAST_NAME": "An",
            "USER_TYPE": "employee",
        }
        client.build_entity_url.side_effect = lambda entity, entity_id: f"https://bitrix/{entity}/{entity_id}/"

        customer = MagicMock()
        customer.name = "12345 - Shop"
        customer.customer_name = "12345 - Shop"
        customer.domain = "shop.myharavan.com"
        customer.custom_haravan_orgid = 12345
        ticket = MagicMock()
        frappe_mock.get_doc.side_effect = [customer, ticket]

        result = refresh_customer_profile("12345 - Shop", ticket="HD-1")

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["bitrix"]["responsible"]["name"], "Nguyen An")
        self.assertEqual(result["data"]["bitrix"]["responsible"]["user_type"], "employee")
        client.get_user.assert_called_once_with("338")
        ticket.set.assert_called_with("custom_responsible", "Nguyen An")
        ticket.save.assert_called_with(ignore_permissions=True)

    @patch("login_with_haravan.engines.customer_enrichment.get_bitrix_config")
    @patch("login_with_haravan.engines.customer_enrichment.BitrixClient")
    def test_inactive_bitrix_responsible_does_not_update_ticket(self, client_cls, config_mock):
        from login_with_haravan.engines.customer_enrichment import refresh_customer_profile

        config_mock.return_value = {
            "enabled": True,
            "configured": True,
            "responsible_configured": True,
        }
        client = client_cls.return_value
        client.find_companies.return_value = [
            {"ID": "42", "TITLE": "Bitrix Company", "ASSIGNED_BY_ID": "338"}
        ]
        client.find_contacts.return_value = []
        client.get_user.return_value = {
            "ID": "338",
            "ACTIVE": False,
            "EMAIL": "owner@example.com",
            "NAME": "Nguyen",
            "LAST_NAME": "An",
            "USER_TYPE": "employee",
        }
        client.build_entity_url.side_effect = lambda entity, entity_id: f"https://bitrix/{entity}/{entity_id}/"

        customer = MagicMock()
        customer.name = "12345 - Shop"
        customer.customer_name = "12345 - Shop"
        customer.domain = "shop.myharavan.com"
        customer.custom_haravan_orgid = 12345
        frappe_mock.get_doc.return_value = customer

        result = refresh_customer_profile("12345 - Shop", ticket="HD-1")

        self.assertTrue(result["success"])
        self.assertFalse(result["data"]["bitrix"]["responsible"]["active"])
        frappe_mock.get_doc.assert_called_once_with("HD Customer", "12345 - Shop")


if __name__ == "__main__":
    unittest.main()
