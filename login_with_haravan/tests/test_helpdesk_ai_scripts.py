import os
import unittest


class TestHelpdeskAiScripts(unittest.TestCase):
    def setUp(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        script_path = os.path.join(root, "scripts", "fix_ai_assist_and_analyze_comment.py")
        with open(script_path, "r", encoding="utf-8") as handle:
            self.content = handle.read()

    def test_reply_copilot_returns_three_ranked_options_in_one_call(self):
        """Reply suggestions should be scenario-aware without extra model calls."""
        self.assertIn("Trong một lần gọi, trả đúng tối đa 3 phương án", self.content)
        self.assertIn("normalize_options(parsed)", self.content)
        self.assertIn('"selected_index": selected_index', self.content)
        self.assertIn("options[:3]", self.content)
        self.assertIn("confidence", self.content)
        self.assertIn("missing_context", self.content)

    def test_reply_copilot_uses_ticket_and_recent_conversation_context(self):
        """The AI prompt should include the ticket body and recent exchanges."""
        self.assertIn('"ticket": ticket_fields', self.content)
        self.assertIn("recent_messages_oldest_to_newest", self.content)
        self.assertIn("internal_notes_oldest_to_newest", self.content)
        self.assertIn("limit=10", self.content)
        self.assertIn("custom_internal_type", self.content)
        self.assertIn("custom_service_name", self.content)

    def test_reply_dialog_has_radio_choices_and_accented_vietnamese(self):
        """Agents should choose among suggested cases in clear Vietnamese UI."""
        self.assertIn('type="radio"', self.content)
        self.assertIn("AI gợi ý trả lời", self.content)
        self.assertIn("Phương án", self.content)
        self.assertIn("Thiếu bối cảnh", self.content)
        self.assertIn("Thêm comment nội bộ", self.content)
        self.assertIn("tiếng Việt có dấu", self.content)
        self.assertIn("không dùng tiếng Việt không dấu", self.content)

    def test_old_unaccented_reply_copy_is_removed(self):
        """Known unaccented Vietnamese copy should not return in the reply flow."""
        forbidden = [
            "AI goi y tra loi",
            "AI Goi y comment",
            "Khong tao duoc goi y comment",
            "Dang tao goi y",
            "Noi dung khong duoc de trong",
            "AI da tao goi y tra loi",
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, self.content)


if __name__ == "__main__":
    unittest.main()
