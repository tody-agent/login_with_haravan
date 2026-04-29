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
