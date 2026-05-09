import unittest

from login_with_haravan.setup.template_safety import escape_template_context


class TemplateSafetyTest(unittest.TestCase):
    def test_escapes_string_payloads(self):
        payload = {
            "subject": "<script>alert(1)</script>",
            "meta": {"onclick": "\" onmouseover=\"alert(1)"},
            "items": ["<img src=x onerror=alert(1)>", "ok"],
        }

        escaped = escape_template_context(payload)

        self.assertEqual(escaped["subject"], "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertEqual(escaped["meta"]["onclick"], "&quot; onmouseover=&quot;alert(1)")
        self.assertEqual(escaped["items"][0], "&lt;img src=x onerror=alert(1)&gt;")
        self.assertEqual(escaped["items"][1], "ok")

    def test_leaves_non_string_values_unchanged(self):
        payload = {"count": 2, "enabled": True, "none_value": None}
        escaped = escape_template_context(payload)

        self.assertEqual(escaped, payload)


if __name__ == "__main__":
    unittest.main()
