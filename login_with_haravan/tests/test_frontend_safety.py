import unittest
import os
import re

class TestFrontendSafety(unittest.TestCase):
    def setUp(self):
        self.public_js_dir = os.path.join(
            os.path.dirname(__file__),
            "../public/js"
        )

    def test_js_syntax_corruption(self):
        """Check for catastrophic syntax corruption in JS files."""
        if not os.path.exists(self.public_js_dir):
            return

        for filename in os.listdir(self.public_js_dir):
            if filename.endswith(".js"):
                filepath = os.path.join(self.public_js_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Rule 1: No single-quote wrapping template string
                # e.g., = '${t('
                self.assertIsNone(
                    re.search(r"=\s*'[^']*?\$\{", content),
                    f"{filename} contains a template string variable syntax inside single quotes."
                )

                # Rule 2: HTML structure integrity
                self.assertIsNone(
                    re.search(r"<\s+[a-zA-Z]", content),
                    f"{filename} contains broken opening HTML tags."
                )
                self.assertIsNone(
                    re.search(r"<\/\s+[a-zA-Z]", content),
                    f"{filename} contains broken closing HTML tags."
                )
                self.assertIsNone(
                    re.search(r"--\s+>", content),
                    f"{filename} contains broken HTML comments."
                )
