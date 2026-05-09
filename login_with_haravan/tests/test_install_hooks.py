import importlib
import sys
import types
import unittest
from unittest.mock import patch


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
        cls._frappe_module = _build_frappe_stub()
        sys.modules["frappe"] = cls._frappe_module
        setattr(cls._frappe_module, "_", lambda text: text)
        cls.install = importlib.import_module("login_with_haravan.setup.install")

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("frappe", None)
        sys.modules.pop("login_with_haravan.setup.install", None)

    def test_after_install_configures_social_login_template_guard_and_deprecation_warning(self):
        with patch.object(self.install, "configure_haravan_social_login") as configure_mock, patch.object(
            self.install, "ensure_default_hd_ticket_template"
        ) as ensure_template_mock, patch.object(
            self.install, "ensure_helpdesk_phone_scripts"
        ) as helpdesk_mock, patch.object(
            self.install, "_warn_helpdesk_auto_provision_deprecated"
        ) as warning_mock:
            self.install.after_install()

        configure_mock.assert_called_once_with()
        ensure_template_mock.assert_called_once_with()
        helpdesk_mock.assert_not_called()
        warning_mock.assert_called_once_with("after_install")

    def test_after_migrate_configures_social_login_template_guard_and_deprecation_warning(self):
        with patch.object(self.install, "configure_haravan_social_login") as configure_mock, patch.object(
            self.install, "ensure_default_hd_ticket_template"
        ) as ensure_template_mock, patch.object(
            self.install, "ensure_helpdesk_phone_scripts"
        ) as helpdesk_mock, patch.object(
            self.install, "_warn_helpdesk_auto_provision_deprecated"
        ) as warning_mock:
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


if __name__ == "__main__":
    unittest.main()
