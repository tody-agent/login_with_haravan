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

    def test_after_install_configures_social_login_only(self):
        with patch.object(self.install, "configure_haravan_social_login") as configure_mock, patch.object(
            self.install, "ensure_helpdesk_phone_scripts"
        ) as helpdesk_mock, patch.object(
            self.install, "_warn_helpdesk_auto_provision_deprecated"
        ) as deprecate_warning_mock:
            self.install.after_install()

        configure_mock.assert_called_once_with()
        helpdesk_mock.assert_not_called()
        deprecate_warning_mock.assert_called_once_with("after_install")

    def test_after_migrate_configures_social_login_only(self):
        with patch.object(self.install, "configure_haravan_social_login") as configure_mock, patch.object(
            self.install, "ensure_helpdesk_phone_scripts"
        ) as helpdesk_mock, patch.object(
            self.install, "_warn_helpdesk_auto_provision_deprecated"
        ) as deprecate_warning_mock:
            self.install.after_migrate()

        configure_mock.assert_called_once_with()
        helpdesk_mock.assert_not_called()
        deprecate_warning_mock.assert_called_once_with("after_migrate")


if __name__ == "__main__":
    unittest.main()
