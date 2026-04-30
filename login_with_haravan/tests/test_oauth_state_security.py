import unittest
import base64
import json
from login_with_haravan.engines.oauth_state import decode_oauth_state

class TestOAuthStateSecurity(unittest.TestCase):
    def test_decode_oauth_state_malformed_base64(self):
        # Invalid base64
        malformed_state = "not-base64-!!!"
        self.assertEqual(decode_oauth_state(malformed_state), {})

    def test_decode_oauth_state_malformed_json(self):
        # Valid base64, but invalid JSON
        malformed_json = "{invalid-json}"
        malformed_state = base64.b64encode(malformed_json.encode('utf-8')).decode('utf-8')
        self.assertEqual(decode_oauth_state(malformed_state), {})

    def test_decode_oauth_state_non_utf8(self):
        # Valid base64, but not UTF-8 after decoding
        non_utf8_bytes = b'\xff\xfe\xfd'
        malformed_state = base64.b64encode(non_utf8_bytes).decode('utf-8')
        self.assertEqual(decode_oauth_state(malformed_state), {})

if __name__ == "__main__":
    unittest.main()
