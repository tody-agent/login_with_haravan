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
                "bitrix_responsible_webhook_url": "responsible-secret",
                "gitlab_token": "gitlab-secret",
            }
        )

        self.assertNotIn("inside", status)
        self.assertTrue(status["ai"]["gemini_api_key"]["configured"])
        self.assertTrue(status["bitrix"]["bitrix_access_token"]["configured"])
        self.assertTrue(status["bitrix"]["bitrix_responsible_webhook_url"]["configured"])
        self.assertTrue(status["gitlab"]["gitlab_token"]["configured"])
        self.assertNotIn("gemini-secret", repr(status))
        self.assertNotIn("bitrix-secret", repr(status))
        self.assertNotIn("responsible-secret", repr(status))
        self.assertNotIn("gitlab-secret", repr(status))

    def test_bitrix_config_reads_helpdesk_settings_customer_and_responsible_webhooks(self):
        from login_with_haravan.engines import site_config

        settings = MagicMock()
        settings.bitrix_base_url = None
        settings.bitrix_domain = None
        settings.bitrix_access_token = None
        settings.bitrix_refresh_token = None
        settings.bitrix_client_id = None
        settings.bitrix_client_secret = None

        def get_password(fieldname, raise_exception=False):
            return {
                "bitrix_webhook_url": "https://haravan.bitrix24.vn/rest/57792/customer-secret/",
                "bitrix_responsible_webhook_url": (
                    "https://haravan.bitrix24.vn/rest/57792/responsible-secret/"
                ),
            }.get(fieldname)

        settings.get_password.side_effect = get_password
        settings.get.side_effect = lambda fieldname: {
            "bitrix_enabled": 1,
            "bitrix_portal_url": "https://haravan.bitrix24.vn",
            "bitrix_timeout_seconds": 9,
        }.get(fieldname)

        def exists(doctype, filters=None):
            if doctype == "DocType" and filters == "Helpdesk Integrations Settings":
                return True
            return None

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.get_doc.return_value = settings

        with patch.object(site_config, "_get_frappe_conf", return_value={}):
            config = site_config.get_bitrix_config()

        self.assertTrue(config["configured"])
        self.assertTrue(config["responsible_configured"])
        self.assertEqual(
            config["webhook_url"],
            "https://haravan.bitrix24.vn/rest/57792/customer-secret/",
        )
        self.assertEqual(
            config["responsible_webhook_url"],
            "https://haravan.bitrix24.vn/rest/57792/responsible-secret/",
        )
        self.assertEqual(config["base_url"], "https://haravan.bitrix24.vn")
        self.assertEqual(config["timeout_seconds"], 9)

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

    def test_setup_grants_all_users_read_select_on_product_suggestion(self):
        from login_with_haravan.setup import install

        class FakeDocPerm:
            def __init__(self):
                self.values = {}
                self.flags = MagicMock()
                self.inserted = False

            def get(self, fieldname):
                return self.values.get(fieldname)

            def set(self, fieldname, value):
                self.values[fieldname] = value

            def insert(self, ignore_permissions=False):
                self.inserted = True

        docperm = FakeDocPerm()

        def exists(doctype, filters=None):
            if doctype == "DocType":
                return True
            if doctype == "Custom DocPerm":
                return None
            return None

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.new_doc.return_value = docperm

        result = install.configure_helpdesk_product_suggestion_permissions()

        self.assertTrue(result["data"]["configured"])
        self.assertTrue(result["data"]["changed"])
        self.assertEqual(docperm.parent, "HD Ticket Product Suggestion")
        self.assertEqual(docperm.parenttype, "DocType")
        self.assertEqual(docperm.parentfield, "permissions")
        self.assertEqual(docperm.role, "All")
        self.assertEqual(docperm.permlevel, 0)
        self.assertEqual(docperm.values["read"], 1)
        self.assertEqual(docperm.values["select"], 1)
        self.assertTrue(docperm.inserted)
        frappe_mock.clear_cache.assert_called_with(doctype="HD Ticket Product Suggestion")
        frappe_mock.db.commit.assert_called()

    def test_setup_skips_product_suggestion_permission_when_doctype_missing(self):
        from login_with_haravan.setup import install

        frappe_mock.db.exists.return_value = None

        result = install.configure_helpdesk_product_suggestion_permissions()

        self.assertFalse(result["data"]["configured"])
        self.assertEqual(result["data"]["reason"], "doctype_missing")
        frappe_mock.new_doc.assert_not_called()

    def test_setup_creates_ticket_cc_field_and_template_row(self):
        from login_with_haravan.setup import install

        class FakeCustomField:
            def __init__(self):
                self.values = {}
                self.flags = MagicMock()
                self.inserted = False

            def update(self, values):
                self.values.update(values)
                for key, value in values.items():
                    setattr(self, key, value)

            def insert(self, ignore_permissions=False):
                self.inserted = True

        class FakeTemplate:
            def __init__(self):
                self.rows = []
                self.saved = False
                self.flags = MagicMock()

            def append(self, fieldname, row):
                self.rows.append((fieldname, row))

            def save(self, ignore_permissions=False):
                self.saved = True

        custom_field = FakeCustomField()
        template = FakeTemplate()

        def exists(doctype, filters=None):
            if doctype == "DocType" and filters == "HD Ticket":
                return True
            if doctype == "Custom Field":
                return None
            if doctype == "HD Ticket Template" and filters == "Default":
                return True
            if doctype == "HD Ticket Template Field":
                return None
            return None

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.new_doc.return_value = custom_field
        frappe_mock.get_doc.return_value = template

        result = install.configure_ticket_cc_metadata()

        self.assertTrue(result["data"]["custom_field_changed"])
        self.assertTrue(result["data"]["template_row_changed"])
        self.assertTrue(custom_field.inserted)
        self.assertEqual(custom_field.values["dt"], "HD Ticket")
        self.assertEqual(custom_field.values["fieldname"], "custom_cc_emails")
        self.assertEqual(custom_field.values["fieldtype"], "Small Text")
        self.assertEqual(template.rows[0][0], "fields")
        self.assertEqual(template.rows[0][1]["fieldname"], "custom_cc_emails")
        self.assertEqual(template.rows[0][1]["hide_from_customer"], 1)
        self.assertTrue(template.saved)
        frappe_mock.db.commit.assert_called()

    def test_setup_creates_helpdesk_integrations_bitrix_config_fields(self):
        from login_with_haravan.setup import install

        class FakeCustomField:
            def __init__(self):
                self.values = {}
                self.flags = MagicMock()
                self.inserted = False

            def update(self, values):
                self.values.update(values)
                for key, value in values.items():
                    setattr(self, key, value)

            def insert(self, ignore_permissions=False):
                self.inserted = True

        created_fields = []

        def exists(doctype, filters=None):
            if doctype == "DocType" and filters == "Helpdesk Integrations Settings":
                return True
            if doctype == "Custom Field":
                return None
            return None

        def new_doc(doctype):
            if doctype == "Custom Field":
                field = FakeCustomField()
                created_fields.append(field)
                return field
            return MagicMock()

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.new_doc.side_effect = new_doc
        frappe_mock.get_meta.return_value.has_field.return_value = False

        result = install.configure_helpdesk_integrations_settings_metadata()

        self.assertTrue(result["data"]["configured"])
        self.assertIn("bitrix_webhook_url", result["data"]["changed_fields"])
        self.assertIn("bitrix_responsible_webhook_url", result["data"]["changed_fields"])
        self.assertEqual(len(created_fields), len(install.HELPDESK_INTEGRATIONS_BITRIX_FIELDS))
        responsible_field = next(
            field for field in created_fields if field.values["fieldname"] == "bitrix_responsible_webhook_url"
        )
        self.assertEqual(responsible_field.values["fieldtype"], "Password")
        self.assertIn("user.get", responsible_field.values["description"])
        frappe_mock.clear_cache.assert_called_with(doctype="Helpdesk Integrations Settings")
        frappe_mock.db.commit.assert_called()

    def test_setup_relabels_existing_standard_bitrix_settings_fields(self):
        from login_with_haravan.setup import install

        class FakePropertySetter:
            def __init__(self):
                self.flags = MagicMock()
                self.inserted = False

            def insert(self, ignore_permissions=False):
                self.inserted = True

        property_setters = []

        def exists(doctype, filters=None):
            if doctype == "DocType" and filters == "Helpdesk Integrations Settings":
                return True
            if doctype == "Custom Field":
                return None
            if doctype == "Property Setter":
                return None
            return None

        def has_field(fieldname):
            return fieldname in {"bitrix_enabled", "bitrix_webhook_url"}

        def new_doc(doctype):
            if doctype == "Property Setter":
                doc = FakePropertySetter()
                property_setters.append(doc)
                return doc
            custom_field = MagicMock()
            custom_field.insert.return_value = None
            return custom_field

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.get_meta.return_value.has_field.side_effect = has_field
        frappe_mock.new_doc.side_effect = new_doc

        result = install.configure_helpdesk_integrations_settings_metadata()

        self.assertIn("bitrix_webhook_url", result["data"]["changed_fields"])
        labels = {
            (doc.field_name, doc.property): doc.value
            for doc in property_setters
        }
        self.assertEqual(
            labels[("bitrix_webhook_url", "label")],
            "Bitrix Customer Inbound Webhook URL",
        )
        self.assertIn("crm.company", labels[("bitrix_webhook_url", "description")])
        self.assertEqual(
            labels[("bitrix_enabled", "label")],
            "Bitrix Enabled",
        )

    def test_bitrix_settings_patch_script_targets_customer_and_responsible_fields(self):
        from scripts.patch_helpdesk_integrations_bitrix_settings import (
            CUSTOM_FIELDS,
            FIELD_PROPERTY_PATCHES,
            custom_field_name,
            property_setter_name,
        )

        property_labels = {
            patch["fieldname"]: patch["label"]
            for patch in FIELD_PROPERTY_PATCHES
        }
        custom_fieldnames = {
            field["fieldname"]: field
            for field in CUSTOM_FIELDS
        }

        self.assertEqual(
            property_labels["bitrix_webhook_url"],
            "Bitrix Customer Inbound Webhook URL",
        )
        self.assertIn("bitrix_responsible_webhook_url", custom_fieldnames)
        self.assertEqual(
            custom_fieldnames["bitrix_responsible_webhook_url"]["fieldtype"],
            "Password",
        )
        self.assertIn(
            "user.get",
            custom_fieldnames["bitrix_responsible_webhook_url"]["description"],
        )
        self.assertEqual(
            custom_field_name("bitrix_responsible_webhook_url"),
            "Helpdesk Integrations Settings-bitrix_responsible_webhook_url",
        )
        self.assertEqual(
            property_setter_name("bitrix_webhook_url", "label"),
            "Helpdesk Integrations Settings-bitrix_webhook_url-label",
        )

    def test_setup_makes_product_suggestion_optional_for_customer_template(self):
        from login_with_haravan.setup import install

        class FakeCustomField:
            def __init__(self):
                self.reqd = 1
                self.flags = MagicMock()
                self.saved = False

            def save(self, ignore_permissions=False):
                self.saved = True

        class FakeTemplateField:
            def __init__(self):
                self.required = 1
                self.flags = MagicMock()
                self.saved = False

            def save(self, ignore_permissions=False):
                self.saved = True

        custom_field = FakeCustomField()
        template_field = FakeTemplateField()

        def exists(doctype, filters=None):
            if doctype == "DocType" and filters == "HD Ticket":
                return True
            if doctype == "Custom Field":
                return "HD Ticket-custom_product_suggestion"
            if doctype == "HD Ticket Template" and filters == "Default":
                return True
            if doctype == "HD Ticket Template Field":
                return "template-row-name"
            return None

        def get_doc(doctype, name):
            if doctype == "Custom Field":
                return custom_field
            if doctype == "HD Ticket Template Field":
                return template_field
            return MagicMock()

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.get_doc.side_effect = get_doc

        result = install.configure_helpdesk_product_suggestion_customer_optional()

        self.assertTrue(result["data"]["custom_field_changed"])
        self.assertTrue(result["data"]["template_row_changed"])
        self.assertEqual(custom_field.reqd, 0)
        self.assertEqual(template_field.required, 0)
        self.assertTrue(custom_field.saved)
        self.assertTrue(template_field.saved)
        frappe_mock.db.commit.assert_called()

    def test_setup_configures_onboarding_service_fields_as_conditional(self):
        from login_with_haravan.setup import install

        class FakeCustomField:
            def __init__(self):
                self.values = {}
                self.flags = MagicMock()
                self.inserted = False

            def update(self, values):
                self.values.update(values)
                for key, value in values.items():
                    setattr(self, key, value)

            def insert(self, ignore_permissions=False):
                self.inserted = True

        class FakeTemplate:
            def __init__(self):
                self.rows = []
                self.saved = False
                self.flags = MagicMock()

            def append(self, fieldname, row):
                self.rows.append((fieldname, row))

            def save(self, ignore_permissions=False):
                self.saved = True

        created_fields = []
        template = FakeTemplate()

        def exists(doctype, filters=None):
            if doctype == "DocType" and filters == "HD Ticket":
                return True
            if doctype == "Custom Field":
                return None
            if doctype == "HD Ticket Template" and filters == "Default":
                return True
            if doctype == "HD Ticket Template Field":
                return None
            return None

        def new_doc(doctype):
            if doctype == "Custom Field":
                field = FakeCustomField()
                created_fields.append(field)
                return field
            return MagicMock()

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.new_doc.side_effect = new_doc
        frappe_mock.get_doc.return_value = template

        result = install.configure_onboarding_service_ticket_metadata()

        expected_fieldnames = [
            "custom_service_group",
            "custom_service_name",
            "custom_service_line",
            "custom_service_onboarding_phrase",
            "custom_service_pricing",
            "custom_service_transaction_id",
            "custom_service_vendor",
            "custom_service_payment_status",
        ]
        self.assertEqual(result["data"]["custom_fields_changed"], expected_fieldnames)
        self.assertEqual(result["data"]["template_rows_changed"], expected_fieldnames)
        self.assertEqual(len(created_fields), len(expected_fieldnames))
        self.assertEqual(len(template.rows), len(expected_fieldnames))

        for custom_field, fieldname in zip(created_fields, expected_fieldnames, strict=True):
            self.assertTrue(custom_field.inserted)
            self.assertEqual(custom_field.values["dt"], "HD Ticket")
            self.assertEqual(custom_field.values["fieldname"], fieldname)
            self.assertEqual(custom_field.values["depends_on"], install.ONBOARDING_SERVICE_DEPENDS_ON)

        for _, row in template.rows:
            self.assertEqual(row["hide_from_customer"], 1)
            self.assertNotIn("depends_on", row)

        frappe_mock.db.commit.assert_called()

    def test_setup_hides_existing_onboarding_service_rows_from_customer_portal(self):
        from login_with_haravan.setup import install

        class FakeTemplateField:
            def __init__(self):
                self.required = 0
                self.hide_from_customer = 0
                self.saved = False
                self.flags = MagicMock()

            def save(self, ignore_permissions=False):
                self.saved = True

        custom_fields_by_name = {}
        fields_by_name = {}

        for field in install.HELPDESK_ONBOARDING_SERVICE_FIELDS:
            doc = MagicMock()
            doc.dt = "HD Ticket"
            for key, value in field.items():
                setattr(doc, key, value)
            custom_fields_by_name[field["fieldname"]] = doc

        def exists(doctype, filters=None):
            if doctype == "DocType" and filters == "HD Ticket":
                return True
            if doctype == "Custom Field":
                return True
            if doctype == "HD Ticket Template" and filters == "Default":
                return True
            if doctype == "HD Ticket Template Field":
                fieldname = filters["fieldname"]
                fields_by_name.setdefault(fieldname, FakeTemplateField())
                return f"template-row-{fieldname}"
            return None

        def get_doc(doctype, name):
            if doctype == "Custom Field":
                fieldname = name.removeprefix("HD Ticket-")
                return custom_fields_by_name[fieldname]
            if doctype == "HD Ticket Template Field":
                fieldname = name.removeprefix("template-row-")
                return fields_by_name[fieldname]
            return MagicMock()

        frappe_mock.db.exists.side_effect = exists
        frappe_mock.get_doc.side_effect = get_doc

        result = install.configure_onboarding_service_ticket_metadata()

        expected_fieldnames = [
            "custom_service_group",
            "custom_service_name",
            "custom_service_line",
            "custom_service_onboarding_phrase",
            "custom_service_pricing",
            "custom_service_transaction_id",
            "custom_service_vendor",
            "custom_service_payment_status",
        ]
        self.assertEqual(result["data"]["custom_fields_changed"], [])
        self.assertEqual(result["data"]["template_rows_changed"], expected_fieldnames)
        for fieldname in expected_fieldnames:
            field = fields_by_name[fieldname]
            self.assertEqual(field.hide_from_customer, 1)
            self.assertTrue(field.saved)

        frappe_mock.db.commit.assert_called()

    def test_portal_field_patch_script_targets_internal_template_rows(self):
        from scripts.hide_customer_portal_internal_ticket_fields import (
            template_field_filters,
            template_field_payload,
        )

        filters = template_field_filters("custom_service_pricing")
        payload = template_field_payload(
            {"fieldname": "custom_service_pricing", "required": 0, "hide_from_customer": 1}
        )

        self.assertIn(["parent", "=", "Default"], filters)
        self.assertIn(["parenttype", "=", "HD Ticket Template"], filters)
        self.assertIn(["parentfield", "=", "fields"], filters)
        self.assertIn(["fieldname", "=", "custom_service_pricing"], filters)
        self.assertEqual(payload, {"required": 0, "hide_from_customer": 1})


if __name__ == "__main__":
    unittest.main()
