import sys
import types
import unittest
from unittest.mock import MagicMock


frappe_mock = sys.modules.get("frappe")
if frappe_mock is None or not isinstance(frappe_mock, MagicMock):
    frappe_mock = MagicMock()
    sys.modules["frappe"] = frappe_mock
    sys.modules["frappe.utils"] = frappe_mock.utils


def _identity_whitelist(*args, **kwargs):
    if args and callable(args[0]):
        return args[0]
    return lambda fn: fn


class TicketCCEngineTest(unittest.TestCase):
    def test_parse_cc_emails_normalizes_separators_case_and_duplicates(self):
        from login_with_haravan.engines.ticket_cc import parse_cc_emails

        result = parse_cc_emails(
            " Owner@Example.COM; support@example.com\nowner@example.com, billing@example.com "
        )

        self.assertEqual(
            result,
            ["owner@example.com", "support@example.com", "billing@example.com"],
        )

    def test_parse_cc_emails_rejects_invalid_addresses(self):
        from login_with_haravan.engines.ticket_cc import InvalidCCEmailError, parse_cc_emails

        with self.assertRaises(InvalidCCEmailError) as ctx:
            parse_cc_emails("valid@example.com, not-an-email")

        self.assertEqual(ctx.exception.invalid_emails, ["not-an-email"])

    def test_merge_cc_removes_primary_recipients_and_preserves_order(self):
        from login_with_haravan.engines.ticket_cc import merge_cc_email_text

        result = merge_cc_email_text(
            ticket_cc="customer@example.com, teammate@example.com, owner@example.com",
            existing_cc="Owner@Example.com, existing@example.com",
            recipients="customer@example.com",
        )

        self.assertEqual(result, "owner@example.com, existing@example.com, teammate@example.com")

    def test_validate_ticket_cc_emails_normalizes_doc_field(self):
        from login_with_haravan.engines.ticket_cc import validate_ticket_cc_emails

        doc = MagicMock()
        doc.custom_cc_emails = "Owner@Example.com; support@example.com"

        validate_ticket_cc_emails(doc)

        self.assertEqual(doc.custom_cc_emails, "owner@example.com, support@example.com")

    def test_created_notification_sends_to_cc_for_portal_ticket(self):
        from login_with_haravan.engines.ticket_cc import send_ticket_cc_created_notification

        doc = types.SimpleNamespace(
            name="51710",
            subject="Test CC email",
            raised_by="customer@example.com",
            via_customer_portal=1,
            custom_cc_emails="customer@example.com, Owner@Example.com",
        )
        frappe_mock.reset_mock()
        frappe_mock.utils.get_url.return_value = "https://haravan.help"

        send_ticket_cc_created_notification(doc)

        frappe_mock.sendmail.assert_called_once()
        kwargs = frappe_mock.sendmail.call_args.kwargs
        self.assertEqual(kwargs["recipients"], ["owner@example.com"])
        self.assertEqual(kwargs["subject"], "[Ticket #51710] Test CC email")
        self.assertEqual(kwargs["reference_doctype"], "HD Ticket")
        self.assertEqual(kwargs["reference_name"], "51710")

    def test_created_notification_skips_native_email_ticket_ack_path(self):
        from login_with_haravan.engines.ticket_cc import send_ticket_cc_created_notification

        doc = types.SimpleNamespace(
            name="EMAIL-1",
            subject="Email ticket",
            raised_by="customer@example.com",
            via_customer_portal=0,
            custom_cc_emails="owner@example.com",
        )
        frappe_mock.reset_mock()

        send_ticket_cc_created_notification(doc)

        frappe_mock.sendmail.assert_not_called()


class TicketCCMixinTest(unittest.TestCase):
    def setUp(self):
        frappe_mock.reset_mock()
        frappe_mock.whitelist.side_effect = _identity_whitelist
        frappe_mock._.side_effect = lambda value: value
        sys.modules.pop("login_with_haravan.overrides.hd_ticket", None)

    def test_reply_via_agent_merges_ticket_cc_before_calling_helpdesk_reply(self):
        from login_with_haravan.overrides.hd_ticket import HDTicketCCMixin

        class BaseTicket:
            raised_by = "customer@example.com"
            custom_cc_emails = "customer@example.com, teammate@example.com"

            def reply_via_agent(self, message, to=None, cc=None, bcc=None, attachments=None):
                self.reply_args = {
                    "message": message,
                    "to": to,
                    "cc": cc,
                    "bcc": bcc,
                    "attachments": attachments,
                }
                return "sent"

        class Ticket(HDTicketCCMixin, BaseTicket):
            pass

        ticket = Ticket()
        result = ticket.reply_via_agent(
            "Hello",
            to="customer@example.com",
            cc="Existing@Example.com",
            bcc="audit@example.com",
            attachments=["FILE-1"],
        )

        self.assertEqual(result, "sent")
        self.assertEqual(ticket.reply_args["cc"], "existing@example.com, teammate@example.com")
        self.assertEqual(ticket.reply_args["to"], "customer@example.com")
        self.assertEqual(ticket.reply_args["bcc"], "audit@example.com")
        self.assertEqual(ticket.reply_args["attachments"], ["FILE-1"])

    def test_acknowledgement_email_includes_ticket_cc_when_present(self):
        self._install_helpdesk_helpers_stub()
        from login_with_haravan.overrides.hd_ticket import HDTicketCCMixin

        class BaseTicket:
            name = "HD-TICKET-1"
            raised_by = "customer@example.com"
            custom_cc_emails = "customer@example.com, owner@example.com"

            def _get_rendered_template(self, content, default_content):
                self.render_args = (content, default_content)
                return "Rendered acknowledgement"

            def send_acknowledgement_email(self):
                self.used_fallback = True

        class Ticket(HDTicketCCMixin, BaseTicket):
            pass

        ticket = Ticket()
        frappe_mock.db.get_single_value.return_value = "Custom acknowledgement"

        ticket.send_acknowledgement_email()

        frappe_mock.sendmail.assert_called_once()
        kwargs = frappe_mock.sendmail.call_args.kwargs
        self.assertEqual(kwargs["recipients"], ["customer@example.com"])
        self.assertEqual(kwargs["cc"], "owner@example.com")
        self.assertEqual(kwargs["reference_doctype"], "HD Ticket")
        self.assertEqual(kwargs["reference_name"], "HD-TICKET-1")
        self.assertEqual(kwargs["message"], "Rendered acknowledgement")
        self.assertFalse(hasattr(ticket, "used_fallback"))

    def test_acknowledgement_email_uses_native_method_when_no_ticket_cc(self):
        from login_with_haravan.overrides.hd_ticket import HDTicketCCMixin

        class BaseTicket:
            raised_by = "customer@example.com"
            custom_cc_emails = ""

            def send_acknowledgement_email(self):
                self.used_fallback = True
                return "native"

        class Ticket(HDTicketCCMixin, BaseTicket):
            pass

        ticket = Ticket()

        result = ticket.send_acknowledgement_email()

        self.assertEqual(result, "native")
        self.assertTrue(ticket.used_fallback)
        frappe_mock.sendmail.assert_not_called()

    @staticmethod
    def _install_helpdesk_helpers_stub():
        module_names = [
            "helpdesk",
            "helpdesk.helpdesk",
            "helpdesk.helpdesk.doctype",
            "helpdesk.helpdesk.doctype.hd_settings",
        ]
        for module_name in module_names:
            module = sys.modules.get(module_name)
            if module is None:
                module = types.ModuleType(module_name)
                module.__path__ = []
                sys.modules[module_name] = module

        helpers = types.ModuleType("helpdesk.helpdesk.doctype.hd_settings.helpers")
        helpers.get_default_email_content = lambda kind: "Default acknowledgement"
        sys.modules["helpdesk.helpdesk.doctype.hd_settings.helpers"] = helpers


if __name__ == "__main__":
    unittest.main()
