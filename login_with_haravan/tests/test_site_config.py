import json
import sys
import unittest
from unittest.mock import MagicMock, patch


frappe_mock = sys.modules.get("frappe")
if frappe_mock is None or not isinstance(frappe_mock, MagicMock):
    frappe_mock = MagicMock()
    sys.modules["frappe"] = frappe_mock
    sys.modules["frappe.utils"] = frappe_mock.utils


class SiteConfigCredentialsTest(unittest.TestCase):
    def setUp(self):
        frappe_mock.reset_mock()
        frappe_mock.db.exists.side_effect = None
        frappe_mock.db.exists.return_value = None
        frappe_mock.get_doc.side_effect = None
        frappe_mock.get_doc.return_value = MagicMock()
        frappe_mock.new_doc.side_effect = None
        frappe_mock.new_doc.return_value = MagicMock()
        frappe_mock.throw.side_effect = RuntimeError
        frappe_mock.whitelist.side_effect = self._identity_whitelist
        frappe_mock.utils.get_url.return_value = (
            "https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan"
        )

    @staticmethod
    def _identity_whitelist(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda fn: fn

    def test_haravan_account_login_json_object_wins(self):
        from login_with_haravan.engines.site_config import get_haravan_login_credentials

        credentials = get_haravan_login_credentials(
            conf={
                "haravan_account_login": {
                    "client_id": "site-client",
                    "client_secret": "site-secret",
                },
                "haravan_login": {
                    "client_id": "old-client",
                    "client_secret": "old-secret",
                },
            }
        )

        self.assertEqual(credentials["client_id"], "site-client")
        self.assertEqual(credentials["client_secret"], "site-secret")
        self.assertEqual(credentials["client_secret_source"], "site_config")

    def test_haravan_login_json_string_and_flat_keys_are_supported(self):
        from login_with_haravan.engines.site_config import get_haravan_login_credentials

        credentials = get_haravan_login_credentials(
            conf={
                "haravan_login": json.dumps({"client_id": "json-client"}),
                "haravan_client_secret": "flat-secret",
            }
        )

        self.assertEqual(credentials["client_id"], "json-client")
        self.assertEqual(credentials["client_secret"], "flat-secret")
        self.assertEqual(credentials["client_id_source"], "site_config")
        self.assertEqual(credentials["client_secret_source"], "site_config")

    def test_haravan_redirect_uri_prefers_grouped_absolute_value(self):
        from login_with_haravan.engines.site_config import get_haravan_redirect_uri_config

        config = get_haravan_redirect_uri_config(
            conf={
                "haravan_account_login": {
                    "client_id": "site-client",
                    "client_secret": "site-secret",
                    "redirect_uri": "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
                }
            }
        )

        self.assertEqual(
            config["redirect_uri"],
            "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
        )
        self.assertEqual(config["source"], "site_config.redirect_uri")

    def test_haravan_redirect_uri_builds_from_configured_public_domain(self):
        from login_with_haravan.engines.site_config import get_haravan_redirect_uri_config

        config = get_haravan_redirect_uri_config(conf={"haravan_public_base_url": "haravan.help"})

        self.assertEqual(
            config["redirect_uri"],
            "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
        )
        self.assertEqual(config["source"], "site_config.public_base_url")

    def test_haravan_public_domain_ignores_stale_absolute_provider_redirect_host(self):
        from login_with_haravan.engines.site_config import get_haravan_redirect_uri_config

        provider_doc = MagicMock()
        provider_doc.redirect_url = (
            "https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan"
        )

        config = get_haravan_redirect_uri_config(
            conf={"haravan_public_base_url": "haravan.help"},
            provider_doc=provider_doc,
        )

        self.assertEqual(
            config["redirect_uri"],
            "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
        )

    def test_haravan_auto_redirect_uri_uses_request_host_not_stale_absolute_provider_host(self):
        from login_with_haravan.engines.site_config import (
            HARAVAN_OAUTH_CALLBACK_PATH,
            get_haravan_redirect_uri_config,
        )

        provider_doc = MagicMock()
        provider_doc.redirect_url = (
            "https://old-domain.example/api/method/login_with_haravan.oauth.login_via_haravan"
        )
        frappe_mock.utils.get_url.return_value = (
            "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan"
        )

        config = get_haravan_redirect_uri_config(conf={}, provider_doc=provider_doc)

        frappe_mock.utils.get_url.assert_called_with(HARAVAN_OAUTH_CALLBACK_PATH)
        self.assertEqual(
            config["redirect_uri"],
            "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
        )
        self.assertEqual(config["source"], "request_host")

    def test_legacy_social_login_key_is_fallback_only(self):
        from login_with_haravan.engines.site_config import get_haravan_login_credentials

        provider_doc = MagicMock()
        provider_doc.client_id = "legacy-client"
        provider_doc.get_password.return_value = "legacy-secret"

        credentials = get_haravan_login_credentials(conf={}, provider_doc=provider_doc)

        self.assertEqual(credentials["client_id"], "legacy-client")
        self.assertEqual(credentials["client_secret"], "legacy-secret")
        self.assertEqual(credentials["client_id_source"], "legacy_doctype")
        self.assertEqual(credentials["client_secret_source"], "legacy_doctype")

    def test_masked_helpdesk_secret_status_never_returns_values(self):
        from login_with_haravan.engines.site_config import get_helpdesk_secret_status

        status = get_helpdesk_secret_status(
            conf={
                "gemini_api_key": "gemini-secret",
                "bitrix_access_token": "bitrix-secret",
                "gitlab_token": "gitlab-secret",
            }
        )

        self.assertNotIn("inside", status)
        self.assertTrue(status["ai"]["gemini_api_key"]["configured"])
        self.assertTrue(status["bitrix"]["bitrix_access_token"]["configured"])
        self.assertTrue(status["gitlab"]["gitlab_token"]["configured"])
        self.assertNotIn("gemini-secret", repr(status))
        self.assertNotIn("bitrix-secret", repr(status))
        self.assertNotIn("gitlab-secret", repr(status))

    def test_generic_secret_helper_prefers_site_config_then_legacy_doctype(self):
        from login_with_haravan.engines.site_config import get_site_or_legacy_secret

        legacy_doc = MagicMock()
        legacy_doc.get_password.return_value = "legacy-token"

        site_value = get_site_or_legacy_secret(
            "bitrix_access_token",
            legacy_doc=legacy_doc,
            legacy_field="access_token",
            conf={"bitrix_access_token": "site-token"},
        )
        fallback_value = get_site_or_legacy_secret(
            "bitrix_access_token",
            legacy_doc=legacy_doc,
            legacy_field="access_token",
            conf={},
        )

        self.assertEqual(site_value, {"value": "site-token", "source": "site_config"})
        self.assertEqual(fallback_value, {"value": "legacy-token", "source": "legacy_doctype"})

    def test_haravan_token_exchange_uses_site_config_secret_before_legacy_doctype(self):
        from login_with_haravan.engines import haravan_api

        provider_doc = MagicMock()
        provider_doc.client_id = "legacy-client"
        provider_doc.get_password.return_value = "legacy-secret"
        provider_doc.redirect_url = "/api/method/login_with_haravan.oauth.login_via_haravan"
        provider_doc.base_url = "https://accounts.haravan.com"
        provider_doc.access_token_url = "/connect/token"
        provider_doc.api_endpoint = "/connect/userinfo"
        frappe_mock.get_doc.return_value = provider_doc

        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "access-token"}
        token_response.raise_for_status.return_value = None
        info_response = MagicMock()
        info_response.json.return_value = {"email": "owner@example.com"}
        info_response.raise_for_status.return_value = None

        requests_mock = MagicMock(
            post=MagicMock(return_value=token_response),
            get=MagicMock(return_value=info_response),
        )
        with patch.object(haravan_api, "requests", requests_mock):
            info, access_token = haravan_api.fetch_haravan_info_and_token(
                "oauth-code",
                conf={
                    "haravan_account_login": {
                        "client_id": "site-client",
                        "client_secret": "site-secret",
                    }
                },
            )

        self.assertEqual(info["email"], "owner@example.com")
        self.assertEqual(access_token, "access-token")
        post_data = requests_mock.post.call_args.kwargs["data"]
        self.assertEqual(post_data["client_id"], "site-client")
        self.assertEqual(post_data["client_secret"], "site-secret")

    def test_haravan_token_exchange_uses_configured_redirect_uri(self):
        from login_with_haravan.engines import haravan_api

        provider_doc = MagicMock()
        provider_doc.client_id = "legacy-client"
        provider_doc.get_password.return_value = "legacy-secret"
        provider_doc.redirect_url = "/api/method/login_with_haravan.oauth.login_via_haravan"
        provider_doc.base_url = "https://accounts.haravan.com"
        provider_doc.access_token_url = "/connect/token"
        provider_doc.api_endpoint = "/connect/userinfo"
        frappe_mock.get_doc.return_value = provider_doc

        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "access-token"}
        token_response.raise_for_status.return_value = None
        info_response = MagicMock()
        info_response.json.return_value = {"email": "owner@example.com"}
        info_response.raise_for_status.return_value = None

        requests_mock = MagicMock(
            post=MagicMock(return_value=token_response),
            get=MagicMock(return_value=info_response),
        )
        with patch.object(haravan_api, "requests", requests_mock):
            haravan_api.fetch_haravan_info_and_token(
                "oauth-code",
                conf={
                    "haravan_account_login": {
                        "client_id": "site-client",
                        "client_secret": "site-secret",
                        "redirect_uri": "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
                    }
                },
            )

        post_data = requests_mock.post.call_args.kwargs["data"]
        self.assertEqual(
            post_data["redirect_uri"],
            "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
        )

    def test_setup_does_not_copy_site_config_secret_into_social_login_key(self):
        from login_with_haravan.setup import install

        class FakeSocialLoginKey:
            def __init__(self):
                self.saved = False
                self.inserted = False
                self.assigned_client_secret = None
                self.enable_social_login = 0
                self.redirect_url = None
                self.flags = MagicMock()
                self.name = "haravan_account"

            def is_new(self):
                return False

            def update(self, values):
                for key, value in values.items():
                    setattr(self, key, value)

            def get_password(self, fieldname, raise_exception=False):
                return None

            def save(self, ignore_permissions=False):
                self.saved = True

            def insert(self, ignore_permissions=False):
                self.inserted = True

            @property
            def client_secret(self):
                return self.assigned_client_secret

            @client_secret.setter
            def client_secret(self, value):
                self.assigned_client_secret = value

        doc = FakeSocialLoginKey()
        frappe_mock.utils.get_url.return_value = "https://haravandesk.s.frappe.cloud/callback"

        with (
            patch.object(install, "_get_or_create_social_login_key", return_value=doc),
            patch.object(
                install,
                "get_haravan_login_credentials",
                return_value={
                    "client_id": "site-client",
                    "client_secret": "site-secret",
                    "client_id_source": "site_config",
                    "client_secret_source": "site_config",
                    "source": "site_config",
                },
            ),
        ):
            result = install.configure_haravan_social_login()

        self.assertTrue(doc.saved)
        self.assertEqual(doc.client_id, "site-client")
        self.assertIsNone(doc.client_secret)
        self.assertTrue(doc.enable_social_login)
        self.assertFalse(result["data"]["client_secret_stored_in_doctype"])

    def test_setup_keeps_social_login_redirect_relative_when_domain_is_configured(self):
        from login_with_haravan.setup import install

        doc = MagicMock()
        doc.name = "haravan_account"
        doc.client_id = "site-client"
        doc.redirect_url = "/api/method/login_with_haravan.oauth.login_via_haravan"
        doc.enable_social_login = 0
        doc.is_new.return_value = False
        doc.get_password.return_value = None

        with (
            patch.object(install, "_get_or_create_social_login_key", return_value=doc),
            patch.object(
                install,
                "get_haravan_login_credentials",
                return_value={
                    "client_id": "site-client",
                    "client_secret": "site-secret",
                    "client_id_source": "site_config",
                    "client_secret_source": "site_config",
                    "source": "site_config",
                },
            ),
            patch.object(
                install,
                "get_haravan_redirect_uri_config",
                return_value={
                    "redirect_uri": "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
                    "source": "site_config.public_base_url",
                },
            ),
        ):
            result = install.configure_haravan_social_login()

        updated_values = doc.update.call_args.args[0]
        self.assertEqual(
            updated_values["redirect_url"],
            "/api/method/login_with_haravan.oauth.login_via_haravan",
        )
        self.assertEqual(
            result["data"]["redirect_url"],
            "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan",
        )

    def test_setup_keeps_legacy_doctype_credentials_as_temporary_fallback(self):
        from login_with_haravan.setup import install

        doc = MagicMock()
        doc.name = "haravan_account"
        doc.client_id = "legacy-client"
        doc.redirect_url = "/api/method/login_with_haravan.oauth.login_via_haravan"
        doc.enable_social_login = 0
        doc.is_new.return_value = False
        doc.get_password.return_value = "legacy-secret"
        frappe_mock.utils.get_url.return_value = "https://haravandesk.s.frappe.cloud/callback"

        credentials_mock = MagicMock(
            return_value={
                "client_id": "legacy-client",
                "client_secret": "legacy-secret",
                "client_id_source": "legacy_doctype",
                "client_secret_source": "legacy_doctype",
                "source": "legacy_doctype",
            }
        )

        with (
            patch.object(install, "_get_or_create_social_login_key", return_value=doc),
            patch.object(install, "get_haravan_login_credentials", credentials_mock),
        ):
            result = install.configure_haravan_social_login()

        credentials_mock.assert_called_once_with(provider_doc=doc)
        updated_values = doc.update.call_args.args[0]
        self.assertEqual(updated_values["enable_social_login"], 1)
        self.assertTrue(result["data"]["client_secret_stored_in_doctype"])


if __name__ == "__main__":
    unittest.main()
