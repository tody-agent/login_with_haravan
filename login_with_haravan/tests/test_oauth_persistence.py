"""Tests for Haravan OAuth post-login persistence."""

import importlib
import sys
import types
import unittest
from unittest.mock import MagicMock


class OAuthPersistenceTest(unittest.TestCase):
    def setUp(self):
        self._saved_modules = {
            name: sys.modules.get(name)
            for name in [
                "frappe",
                "frappe.utils",
                "frappe.utils.oauth",
                "frappe.www",
                "frappe.www.login",
                "login_with_haravan.oauth",
                "login_with_haravan.engines.haravan_api",
                "login_with_haravan.engines.sync_helpdesk",
            ]
        }

        frappe = types.ModuleType("frappe")
        frappe.session = types.SimpleNamespace(user="Guest")
        frappe.db = MagicMock()
        frappe.log_error = MagicMock()
        frappe.get_traceback = MagicMock(return_value="traceback")
        frappe.throw = MagicMock(side_effect=Exception("frappe.throw"))
        frappe.whitelist = lambda **_kwargs: (lambda fn: fn)
        frappe._ = lambda text: text
        frappe.utils = types.ModuleType("frappe.utils")
        frappe.utils.get_url = MagicMock(side_effect=lambda path: f"https://haravan.help{path}")
        frappe.utils.now_datetime = MagicMock(return_value="2026-05-07 18:30:00")

        oauth_utils = types.ModuleType("frappe.utils.oauth")
        oauth_utils.get_info_via_oauth = MagicMock()
        oauth_utils.login_oauth_user = MagicMock()

        www = types.ModuleType("frappe.www")
        login = types.ModuleType("frappe.www.login")
        login.sanitize_redirect = MagicMock(side_effect=lambda value: value)

        sys.modules["frappe"] = frappe
        sys.modules["frappe.utils"] = frappe.utils
        sys.modules["frappe.utils.oauth"] = oauth_utils
        sys.modules["frappe.www"] = www
        sys.modules["frappe.www.login"] = login

        self.frappe = frappe

        import login_with_haravan.oauth as oauth

        self.oauth = importlib.reload(oauth)

    def tearDown(self):
        for name, module in self._saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        engines = sys.modules.get("login_with_haravan.engines")
        if engines:
            if self._saved_modules["login_with_haravan.engines.haravan_api"] is None:
                engines.__dict__.pop("haravan_api", None)
            if self._saved_modules["login_with_haravan.engines.sync_helpdesk"] is None:
                engines.__dict__.pop("sync_helpdesk", None)

    def test_post_login_persistence_commits_after_helpdesk_sync(self):
        """OAuth callback is GET; app-owned writes need their own durable commit."""
        self.oauth.enrich_helpdesk_data = MagicMock(return_value="Partner-Hailm - 1000409653")
        self.oauth.upsert_haravan_account_link = MagicMock()

        self.oauth._persist_after_login(
            {
                "email": "leminhhai@gmail.com",
                "sub": "1000579770",
                "orgid": "1000409653",
                "orgname": "Partner-Hailm",
                "role": "owner",
            },
            user="leminhhai@gmail.com",
        )

        self.oauth.enrich_helpdesk_data.assert_called_once()
        self.oauth.upsert_haravan_account_link.assert_called_once()
        self.frappe.db.commit.assert_called_once()

    def test_post_login_persistence_skips_guest_without_commit(self):
        self.oauth._persist_after_login({}, user="Guest")

        self.frappe.db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
