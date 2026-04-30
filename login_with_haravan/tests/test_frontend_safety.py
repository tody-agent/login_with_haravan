import unittest
import os
import re

class TestFrontendSafety(unittest.TestCase):
    def setUp(self):
        self.public_js_dir = os.path.join(
            os.path.dirname(__file__),
            "../public/js"
        )

    def read_js(self, filename):
        filepath = os.path.join(self.public_js_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

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

    def test_haravan_login_script_rewrites_redirect_uri_for_custom_domain(self):
        """The login page script should repair stale Frappe Cloud redirect_uri values."""
        content = self.read_js("haravan_login_redirect.js")

        self.assertIn("redirect_uri", content)
        self.assertIn("frappe.cloud", content)
        self.assertIn("login_with_haravan.oauth.login_via_haravan", content)

    def test_helpdesk_vi_override_is_registered_last(self):
        hooks_path = os.path.join(os.path.dirname(__file__), "../hooks.py")
        with open(hooks_path, "r", encoding="utf-8") as f:
            content = f.read()

        profile_panel = "/assets/login_with_haravan/js/customer_profile_panel.js"
        vi_override = "/assets/login_with_haravan/js/helpdesk_vi_override.js"

        self.assertIn(vi_override, content)
        self.assertLess(content.index(profile_panel), content.index(vi_override))

    def test_helpdesk_vi_override_has_scoped_guards(self):
        content = self.read_js("helpdesk_vi_override.js")

        for token in [
            "HaravanHelpdeskViOverride",
            "HARAVAN_HELPDESK_VI_OVERRIDE_DISABLED",
            "haravan_helpdesk_vi_override_disabled",
            "/helpdesk/my-tickets",
            "/helpdesk/my-tickets/new",
            "/my-tickets",
            "/my-tickets/new",
            "isTargetRoute",
            "isVietnameseLocale",
            "hasVietnamesePageSignal",
            "shouldActivate",
            "MutationObserver",
        ]:
            self.assertIn(token, content)

        for token in ["vi", "vietnamese", "tiếng việt", "tieng viet"]:
            self.assertIn(token, content.lower())

    def test_helpdesk_vi_override_dictionary_covers_visible_customer_portal_terms(self):
        content = self.read_js("helpdesk_vi_override.js")

        for token in [
            "Create",
            "Tạo yêu cầu",
            "Filter",
            "Bộ lọc",
            "Columns",
            "Cột",
            "Last Modified",
            "Cập nhật gần nhất",
            "Empty - Choose a field to filter by",
            "Chưa có bộ lọc - Chọn trường để lọc",
            "Add Filter",
            "Search",
            "Tìm kiếm",
            "Subject",
            "Tiêu đề",
            "Status",
            "Trạng thái",
            "Priority",
            "Mức ưu tiên",
            "Ticket Type",
            "Loại yêu cầu",
            "Product Suggestion",
            "Sản phẩm liên quan",
            "Shop / MyHaravan domain",
            "Tên miền Shop / MyHaravan",
            "First response",
            "Phản hồi đầu tiên",
            "Resolution",
            "Giải quyết",
            "Resolution By",
            "Hạn giải quyết",
            "Response By",
            "Hạn phản hồi",
            "Open",
            "Đang mở",
            "Resolved",
            "Đã xử lý",
            "Medium",
            "Trung bình",
            "Nhóm (Group)",
            "Sản phẩm liên quan (Suggestion)",
            "Loại yêu cầu (Type)",
            "in 4 days",
            "trong ",
            "ago",
            "trước",
        ]:
            self.assertIn(token, content)

    def test_helpdesk_vi_override_avoids_user_content_and_unsafe_dom_apis(self):
        content = self.read_js("helpdesk_vi_override.js")

        for token in [
            "CONTENT_SKIP_SELECTOR",
            "TEXT_SKIP_SELECTOR",
            "input",
            "textarea",
            "contenteditable",
            "ProseMirror",
            "ticket-subject",
            "ticket-description",
            "data-haravan-no-translate",
            "data-haravan-user-content",
        ]:
            self.assertIn(token, content)

        for pattern in [
            r"\.innerHTML\s*=",
            r"\beval\s*\(",
            r"new\s+Function\s*\(",
            r"document\.write\s*\(",
            r"setAttribute\s*\(\s*['\"]on",
        ]:
            self.assertIsNone(
                re.search(pattern, content),
                "helpdesk_vi_override.js should not use unsafe DOM/code APIs."
            )
