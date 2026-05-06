import unittest
import ast
import os

class TestApiRoutes(unittest.TestCase):
    def test_oauth_module_syntax_and_structure(self):
        """Ensure oauth.py module compiles and has expected whitelisted methods."""
        oauth_path = os.path.join(
            os.path.dirname(__file__),
            "../oauth.py"
        )
        if not os.path.exists(oauth_path):
            self.fail("oauth.py not found")

        with open(oauth_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            self.fail(f"SyntaxError in oauth.py: {e}")

        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        function_names = [f.name for f in functions]

        # Check if the required methods exist
        self.assertIn("login_via_haravan", function_names)
        self.assertIn("get_user_haravan_org_options", function_names)

        # Verify that they are whitelisted
        for func in functions:
            if func.name in ["login_via_haravan"]:
                decorators = []
                for dec in func.decorator_list:
                    if isinstance(dec, ast.Attribute) and getattr(dec.value, "id", "") == "frappe" and dec.attr == "whitelist":
                        decorators.append("frappe.whitelist")
                    elif isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Attribute) and getattr(dec.func.value, "id", "") == "frappe" and dec.func.attr == "whitelist":
                            decorators.append("frappe.whitelist")
                self.assertIn("frappe.whitelist", decorators, f"{func.name} is missing @frappe.whitelist decorator")

    def test_oauth_callback_does_not_fetch_haravan_shop_data(self):
        """Haravan OAuth is login-only; customer profile enrichment is Bitrix on-demand."""
        oauth_path = os.path.join(os.path.dirname(__file__), "../oauth.py")
        with open(oauth_path, "r", encoding="utf-8") as f:
            source = f.read()

        self.assertNotIn("fetch_org_and_subscription_data", source)
        self.assertNotIn("haravan_org_data", source)

    def test_haravan_social_login_scope_is_login_only(self):
        """Commerce scopes must not be requested for the login-only OAuth provider."""
        install_path = os.path.join(os.path.dirname(__file__), "../setup/install.py")
        with open(install_path, "r", encoding="utf-8") as f:
            source = f.read()

        self.assertIn("openid profile email org userinfo", source)
        self.assertNotIn("com.read_shop", source)

    def test_portal_customer_options_use_contact_links(self):
        """Customer portal options should include HD Customers linked to the user's Contact."""
        oauth_path = os.path.join(os.path.dirname(__file__), "../oauth.py")
        with open(oauth_path, "r", encoding="utf-8") as f:
            source = f.read()

        self.assertIn("get_user_haravan_org_options", source)
        self.assertIn("Contact Email", source)
        self.assertIn("Dynamic Link", source)
        self.assertIn('"link_doctype": "HD Customer"', source)
        self.assertIn("return list(orgs_by_customer.values())", source)
        self.assertIn("get_contact_phone_options", source)
        self.assertIn('"phone": phone_options[0] if phone_options else ""', source)
        self.assertIn('"phone_options": phone_options', source)

        install_path = os.path.join(os.path.dirname(__file__), "../setup/install.py")
        with open(install_path, "r", encoding="utf-8") as f:
            install_source = f.read()

        self.assertIn(
            '"url_method": "login_with_haravan.oauth.get_user_haravan_org_options"',
            install_source,
        )

    def test_oauth_persistence_uses_profile_email_not_session_only(self):
        """Post-login sync must not silently skip while the callback session is Guest."""
        oauth_path = os.path.join(os.path.dirname(__file__), "../oauth.py")
        with open(oauth_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        login_callback = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "login_via_haravan"
        )
        persist_calls = [
            node for node in ast.walk(login_callback)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_persist_after_login"
        ]

        self.assertEqual(len(persist_calls), 1)
        self.assertTrue(
            any(
                keyword.arg == "user"
                and isinstance(keyword.value, ast.Call)
                and isinstance(keyword.value.func, ast.Attribute)
                and keyword.value.func.attr == "get"
                and isinstance(keyword.value.func.value, ast.Name)
                and keyword.value.func.value.id == "profile"
                for keyword in persist_calls[0].keywords
            ),
            "_persist_after_login must receive user=profile.get(...)",
        )
