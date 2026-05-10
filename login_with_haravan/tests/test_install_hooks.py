import importlib
import sys
import types
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch


_INSTALL_HOOK_CONFIGURE_FUNCTIONS = (
    "configure_haravan_social_login",
    "configure_customer_profile_metadata",
    "configure_helpdesk_integrations_settings_metadata",
    "configure_helpdesk_product_suggestion_permissions",
    "configure_ticket_customer_template_metadata",
    "configure_helpdesk_product_suggestion_customer_optional",
    "configure_ticket_cc_metadata",
    "configure_onboarding_service_ticket_metadata",
)


def _build_frappe_stub():
    frappe_module = types.ModuleType("frappe")
    frappe_module.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    frappe_module.throw = lambda message: (_ for _ in ()).throw(RuntimeError(message))
    frappe_module._dict = dict
    frappe_module.conf = {}
    frappe_module.db = types.SimpleNamespace()
    frappe_module.utils = types.SimpleNamespace(get_url=lambda value: value)

    return frappe_module


class InstallHooksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._frappe_module_previous = sys.modules.get("frappe")
        cls._frappe_module = _build_frappe_stub()
        sys.modules["frappe"] = cls._frappe_module
        setattr(cls._frappe_module, "_", lambda text: text)
        cls.install = importlib.import_module("login_with_haravan.setup.install")

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("login_with_haravan.setup.install", None)
        if cls._frappe_module_previous is not None:
            sys.modules["frappe"] = cls._frappe_module_previous
        else:
            sys.modules.pop("frappe", None)

    def test_after_install_configures_social_login_template_guard_and_deprecation_warning(self):
        with ExitStack() as stack:
            configure_mock = stack.enter_context(
                patch.object(self.install, "configure_haravan_social_login")
            )
            for name in _INSTALL_HOOK_CONFIGURE_FUNCTIONS[1:]:
                stack.enter_context(patch.object(self.install, name))
            ensure_template_mock = stack.enter_context(
                patch.object(self.install, "ensure_default_hd_ticket_template")
            )
            helpdesk_mock = stack.enter_context(patch.object(self.install, "ensure_helpdesk_phone_scripts"))
            warning_mock = stack.enter_context(
                patch.object(self.install, "_warn_helpdesk_auto_provision_deprecated")
            )
            self.install.after_install()

        configure_mock.assert_called_once_with()
        ensure_template_mock.assert_called_once_with()
        helpdesk_mock.assert_not_called()
        warning_mock.assert_called_once_with("after_install")

    def test_after_migrate_configures_social_login_template_guard_and_deprecation_warning(self):
        with ExitStack() as stack:
            configure_mock = stack.enter_context(
                patch.object(self.install, "configure_haravan_social_login")
            )
            for name in _INSTALL_HOOK_CONFIGURE_FUNCTIONS[1:]:
                stack.enter_context(patch.object(self.install, name))
            ensure_template_mock = stack.enter_context(
                patch.object(self.install, "ensure_default_hd_ticket_template")
            )
            helpdesk_mock = stack.enter_context(patch.object(self.install, "ensure_helpdesk_phone_scripts"))
            warning_mock = stack.enter_context(
                patch.object(self.install, "_warn_helpdesk_auto_provision_deprecated")
            )
            self.install.after_migrate()

        configure_mock.assert_called_once_with()
        ensure_template_mock.assert_called_once_with()
        helpdesk_mock.assert_not_called()
        warning_mock.assert_called_once_with("after_migrate")

    def test_template_guard_skips_when_default_exists(self):
        exists_values = {
            ("DocType", self.install.HDTICKET_TEMPLATE_DOCTYPE): True,
            (self.install.HDTICKET_TEMPLATE_DOCTYPE, self.install.HDTICKET_TEMPLATE_DOCNAME): True,
        }

        with patch.object(
            self.install.frappe.db,
            "exists",
            side_effect=lambda doctype, name: exists_values.get((doctype, name), False),
            create=True,
        ), patch.object(self.install.frappe, "new_doc", create=True) as new_doc_mock:
            result = self.install.ensure_default_hd_ticket_template()

        self.assertEqual(result["status"], "skipped_existing")
        new_doc_mock.assert_not_called()

    def test_template_guard_creates_default_once(self):
        exists_values = {
            ("DocType", self.install.HDTICKET_TEMPLATE_DOCTYPE): True,
            (self.install.HDTICKET_TEMPLATE_DOCTYPE, self.install.HDTICKET_TEMPLATE_DOCNAME): False,
        }

        doc = types.SimpleNamespace(
            name=None,
            flags=types.SimpleNamespace(),
            set=lambda field, value: None,
            insert=lambda **kwargs: None,
        )

        with patch.object(
            self.install.frappe.db,
            "exists",
            side_effect=lambda doctype, name: exists_values.get((doctype, name), False),
            create=True,
        ), patch.object(self.install, "_has_meta_field", return_value=True), patch.object(
            self.install.frappe, "new_doc", return_value=doc, create=True
        ):
            result = self.install.ensure_default_hd_ticket_template()

        self.assertEqual(result["status"], "created")
        self.assertEqual(result["name"], self.install.HDTICKET_TEMPLATE_DOCNAME)

    def test_ensure_helpdesk_phone_scripts_skips_when_hd_ticket_doctype_missing(self):
        with patch.object(self.install.frappe.db, "exists", return_value=False, create=True), patch.object(
            self.install, "_upsert_client_script"
        ) as client_mock, patch.object(self.install, "_upsert_server_script") as server_mock:
            self.install.ensure_helpdesk_phone_scripts()

        client_mock.assert_not_called()
        server_mock.assert_not_called()

    def test_ensure_helpdesk_phone_scripts_runs_only_available_script_doctypes(self):
        exists_values = {
            ("DocType", "HD Ticket"): True,
            ("DocType", "Client Script"): True,
            ("DocType", "Server Script"): False,
        }
        with patch.object(
            self.install.frappe.db,
            "exists",
            side_effect=lambda doctype, name: exists_values.get((doctype, name), False),
            create=True,
        ), patch.object(self.install, "_upsert_client_script") as client_mock, patch.object(
            self.install, "_upsert_server_script"
        ) as server_mock:
            self.install.ensure_helpdesk_phone_scripts()

        client_mock.assert_called_once_with()
        server_mock.assert_not_called()

    def test_upsert_client_script_updates_existing_named_doc(self):
        existing_doc = Mock()
        existing_doc.is_new.return_value = False
        existing_doc.flags = types.SimpleNamespace()

        with patch.object(self.install, "_build_client_script_code", return_value="client-script"), patch.object(
            self.install, "_get_or_new_named_doc", return_value=existing_doc
        ), patch.object(self.install, "_has_meta_field", return_value=True), patch.object(
            self.install, "_save_named_doc"
        ) as save_mock:
            self.install._upsert_client_script()

        existing_doc.update.assert_called_once_with(
            {
                "dt": "HD Ticket",
                "enabled": 1,
                "script": "client-script",
                "view": "Form",
            }
        )
        save_mock.assert_called_once_with(existing_doc)

    def test_upsert_server_script_updates_existing_named_doc(self):
        existing_doc = Mock()
        existing_doc.is_new.return_value = False
        existing_doc.flags = types.SimpleNamespace()

        with patch.object(self.install, "_build_server_script_code", return_value="server-script"), patch.object(
            self.install, "_get_or_new_named_doc", return_value=existing_doc
        ), patch.object(self.install, "_save_named_doc") as save_mock:
            self.install._upsert_server_script()

        existing_doc.update.assert_called_once_with(
            {
                "script_type": "DocType Event",
                "reference_doctype": "HD Ticket",
                "doctype_event": "Before Insert",
                "enabled": 1,
                "script": "server-script",
            }
        )
        save_mock.assert_called_once_with(existing_doc)


if __name__ == "__main__":
    unittest.main()
