"""Unit tests for Helpdesk ticket autofill."""

import sys
import unittest
from unittest.mock import MagicMock, patch


frappe_mock = sys.modules.get("frappe")
if frappe_mock is None or not isinstance(frappe_mock, MagicMock):
    frappe_mock = MagicMock()
    frappe_mock.DuplicateEntryError = type("DuplicateEntryError", (Exception,), {})
    sys.modules["frappe"] = frappe_mock
    sys.modules["frappe.utils"] = frappe_mock.utils


def _reset_frappe_mock():
    frappe_mock.reset_mock()
    frappe_mock.db.get_value.side_effect = None
    frappe_mock.db.get_value.return_value = None
    frappe_mock.get_meta.side_effect = None
    frappe_mock.get_meta.return_value = MagicMock(fields=[])


class FakeDoc:
    def __init__(self, **values):
        self.values = dict(values)

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value


class TestProductSuggestionParser(unittest.TestCase):
    def test_parses_bracket_colon_format(self):
        from login_with_haravan.engines.ticket_autofill import parse_product_suggestion

        result = parse_product_suggestion("[HaraInventory]:Apps-Social Login")

        self.assertEqual(result["product_line"], "HaraInventory")
        self.assertEqual(result["product_feature"], "Apps-Social Login")

    def test_parses_plain_colon_format(self):
        from login_with_haravan.engines.ticket_autofill import parse_product_suggestion

        result = parse_product_suggestion("HaraRetail: POS")

        self.assertEqual(result["product_line"], "HaraRetail")
        self.assertEqual(result["product_feature"], "POS")

    def test_empty_product_suggestion_is_ignored(self):
        from login_with_haravan.engines.ticket_autofill import parse_product_suggestion

        result = parse_product_suggestion("")

        self.assertIsNone(result["product_line"])
        self.assertIsNone(result["product_feature"])


class TestCustomerResolution(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    def test_normalizes_numeric_org_to_myharavan_domain(self):
        from login_with_haravan.engines.ticket_autofill import normalize_domain

        self.assertEqual(normalize_domain("200000376735"), "200000376735.myharavan.com")

    def test_resolves_customer_by_myharavan_domain(self):
        from login_with_haravan.engines.ticket_autofill import resolve_customer_from_link

        frappe_mock.db.get_value.side_effect = [
            {
                "name": "200000376735 - Test Shop",
                "domain": "test.myharavan.com",
                "custom_myharavan": "test.myharavan.com",
                "custom_haravan_orgid": 200000376735,
            }
        ]

        result = resolve_customer_from_link("https://test.myharavan.com/admin")

        self.assertEqual(result["customer"], "200000376735 - Test Shop")
        self.assertEqual(result["org_id"], "200000376735")
        self.assertEqual(result["myharavan_domain"], "test.myharavan.com")

    def test_returns_partial_data_when_customer_not_found(self):
        from login_with_haravan.engines.ticket_autofill import resolve_customer_from_link

        frappe_mock.db.get_value.return_value = None

        result = resolve_customer_from_link("200000376735")

        self.assertIsNone(result["customer"])
        self.assertEqual(result["org_id"], "200000376735")
        self.assertEqual(result["myharavan_domain"], "200000376735.myharavan.com")


class TestAutoFillTicketFields(unittest.TestCase):
    def setUp(self):
        _reset_frappe_mock()

    @patch("login_with_haravan.engines.ticket_autofill.get_ticket_field_map")
    def test_auto_fills_customer_and_product_fields(self, mock_field_map):
        from login_with_haravan.engines.ticket_autofill import auto_fill_ticket_fields

        mock_field_map.return_value = {
            "link_web_myharavan": "custom_link_web_myharavan",
            "customer": "customer",
            "org_id": "custom_org_id",
            "myharavan_domain": "custom_myharavan_domain",
            "product_suggestion": "custom_product_suggestion",
            "product_line": "custom_product_line",
            "product_feature": "custom_product_feature",
        }
        frappe_mock.db.get_value.return_value = {
            "name": "200000376735 - Test Shop",
            "domain": "test.myharavan.com",
            "custom_myharavan": "test.myharavan.com",
            "custom_haravan_orgid": 200000376735,
        }
        doc = FakeDoc(
            doctype="HD Ticket",
            custom_link_web_myharavan="test.myharavan.com",
            custom_product_suggestion="[HaraInventory]:Apps-Social Login",
        )

        auto_fill_ticket_fields(doc)

        self.assertEqual(doc.values["customer"], "200000376735 - Test Shop")
        self.assertEqual(doc.values["custom_org_id"], "200000376735")
        self.assertEqual(doc.values["custom_myharavan_domain"], "test.myharavan.com")
        self.assertEqual(doc.values["custom_product_line"], "HaraInventory")
        self.assertEqual(doc.values["custom_product_feature"], "Apps-Social Login")

    @patch("login_with_haravan.engines.ticket_autofill.get_ticket_field_map")
    def test_auto_fill_does_not_override_manual_customer(self, mock_field_map):
        from login_with_haravan.engines.ticket_autofill import auto_fill_ticket_fields

        mock_field_map.return_value = {
            "link_web_myharavan": "custom_link_web_myharavan",
            "customer": "customer",
            "org_id": "custom_org_id",
            "myharavan_domain": "custom_myharavan_domain",
            "product_suggestion": "custom_product_suggestion",
            "product_line": "custom_product_line",
            "product_feature": "custom_product_feature",
        }
        frappe_mock.db.get_value.return_value = {
            "name": "Resolved Customer",
            "domain": "test.myharavan.com",
            "custom_myharavan": "test.myharavan.com",
            "custom_haravan_orgid": 200000376735,
        }
        doc = FakeDoc(
            doctype="HD Ticket",
            customer="Manual Customer",
            custom_link_web_myharavan="test.myharavan.com",
            custom_product_suggestion="[HaraInventory]:Apps-Social Login",
        )

        auto_fill_ticket_fields(doc)

        self.assertEqual(doc.values["customer"], "Manual Customer")
        self.assertEqual(doc.values["custom_product_line"], "HaraInventory")


if __name__ == "__main__":
    unittest.main()
