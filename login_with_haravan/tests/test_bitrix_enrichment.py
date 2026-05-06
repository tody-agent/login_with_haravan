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
    frappe_mock.has_permission.side_effect = None
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


class BitrixClientTest(unittest.TestCase):
    @patch("login_with_haravan.engines.bitrix_api.requests.get")
    def test_responsible_user_get_accepts_full_template_url(self, get_mock):
        from login_with_haravan.engines.bitrix_api import BitrixClient

        response = MagicMock()
        response.json.return_value = {
            "result": [
                {
                    "ID": "338",
                    "ACTIVE": True,
                    "EMAIL": "owner@example.com",
                    "NAME": "Nguyen",
                    "LAST_NAME": "An",
                    "USER_TYPE": "employee",
                }
            ]
        }
        response.raise_for_status.return_value = None
        get_mock.return_value = response

        client = BitrixClient(
            {
                "responsible_webhook_url": (
                    "https://haravan.bitrix24.vn/rest/57792/secret/user.get.json?ID={ASSIGNED_BY_ID}"
                ),
                "timeout_seconds": 7,
            }
        )

        result = client.get_user("338")

        self.assertEqual(result["EMAIL"], "owner@example.com")
        get_mock.assert_called_once_with(
            "https://haravan.bitrix24.vn/rest/57792/secret/user.get.json?ID=338",
            timeout=7,
        )

    @patch("login_with_haravan.engines.bitrix_api.requests.get")
    def test_responsible_user_get_adds_id_to_full_method_url_without_query(self, get_mock):
        from login_with_haravan.engines.bitrix_api import BitrixClient

        response = MagicMock()
        response.json.return_value = {"result": []}
        response.raise_for_status.return_value = None
        get_mock.return_value = response

        client = BitrixClient(
            {
                "responsible_webhook_url": "https://haravan.bitrix24.vn/rest/57792/secret/user.get.json",
            }
        )

        self.assertIsNone(client.get_user("338"))
        get_mock.assert_called_once_with(
            "https://haravan.bitrix24.vn/rest/57792/secret/user.get.json?ID=338",
            timeout=15,
        )


class CustomerEnrichmentTest(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    def test_refresh_checks_hd_customer_permission_before_loading_doc(self):
        from login_with_haravan.engines.customer_enrichment import refresh_customer_profile

        frappe_mock.has_permission.side_effect = PermissionError("denied")

        with self.assertRaises(PermissionError):
            refresh_customer_profile("12345 - Shop")

        frappe_mock.has_permission.assert_called_once_with(
            "HD Customer",
            "read",
            "12345 - Shop",
            throw=True,
        )
        frappe_mock.get_doc.assert_not_called()

    def test_refresh_checks_contact_permission_before_loading_contact_doc(self):
        from login_with_haravan.engines.customer_enrichment import refresh_customer_profile

        customer = MagicMock()
        customer.name = "12345 - Shop"
        frappe_mock.get_doc.return_value = customer

        def deny_contact(doctype, *_args, **_kwargs):
            if doctype == "Contact":
                raise PermissionError("denied")
            return True

        frappe_mock.has_permission.side_effect = deny_contact

        with self.assertRaises(PermissionError):
            refresh_customer_profile("12345 - Shop", "owner@example.com")

        self.assertEqual(frappe_mock.get_doc.call_count, 1)
        frappe_mock.get_doc.assert_called_once_with("HD Customer", "12345 - Shop")

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
    def test_profile_open_uses_local_customer_without_bitrix_fetch(self, client_cls, config_mock):
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
        self.assertEqual(result["data"]["customer"]["name"], "12345 - Shop")
        client.find_companies.assert_not_called()
        client.find_contacts.assert_not_called()

    @patch("login_with_haravan.engines.customer_enrichment.get_bitrix_config")
    @patch("login_with_haravan.engines.customer_enrichment.BitrixClient")
    def test_missing_hd_customer_can_fetch_bitrix_by_ticket_orgid(self, client_cls, config_mock):
        from login_with_haravan.engines.customer_enrichment import get_ticket_bitrix_profile

        config_mock.return_value = {
            "enabled": True,
            "configured": True,
            "responsible_configured": False,
        }
        client = client_cls.return_value
        client.find_companies.return_value = [
            {"ID": "42", "TITLE": "Bitrix Company", "ASSIGNED_BY_ID": "338"}
        ]
        client.find_contacts.return_value = [
            {"ID": "77", "NAME": "Owner", "EMAIL": [{"VALUE": "owner@example.com"}]}
        ]
        client.build_entity_url.side_effect = lambda entity, entity_id: f"https://bitrix/{entity}/{entity_id}/"
        frappe_mock.db.get_value.side_effect = [
            {"customer": None, "contact": "owner@example.com", "raised_by": "owner@example.com"},
            "12345",
            None,
        ]

        contact = MagicMock()
        contact.name = "owner@example.com"
        contact.email_id = "owner@example.com"
        contact.phone = ""
        contact.mobile_no = ""
        frappe_mock.get_doc.return_value = contact

        result = get_ticket_bitrix_profile("HD-1")

        self.assertTrue(result["success"])
        self.assertIsNone(result["data"]["customer"])
        self.assertEqual(result["data"]["bitrix"]["company"]["id"], "42")
        self.assertEqual(result["data"]["bitrix"]["contact"]["id"], "77")
        client.find_companies.assert_called_once_with(haravan_orgid="12345")

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
        self.assertEqual(result["data"]["bitrix"]["responsible"]["email"], "owner@example.com")
        self.assertEqual(result["data"]["bitrix"]["responsible"]["user_type"], "employee")
        client.get_user.assert_called_once_with("338")
        ticket.set.assert_called_with("custom_responsible", "owner@example.com")
        ticket.save.assert_called_with(ignore_permissions=True)

    @patch("login_with_haravan.engines.customer_enrichment.get_bitrix_config")
    @patch("login_with_haravan.engines.customer_enrichment.BitrixClient")
    def test_active_bitrix_responsible_without_email_does_not_update_ticket(self, client_cls, config_mock):
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
            "EMAIL": "",
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
        self.assertEqual(result["data"]["bitrix"]["responsible"]["name"], "Nguyen An")
        frappe_mock.get_doc.assert_called_once_with("HD Customer", "12345 - Shop")

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
