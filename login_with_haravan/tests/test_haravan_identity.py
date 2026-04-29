import json
import unittest

from login_with_haravan.engines.haravan_identity import (
    HaravanIdentityError,
    build_link_fields,
    make_link_name,
    normalize_haravan_profile,
)
from login_with_haravan.engines.oauth_payload import decode_json_payload
from login_with_haravan.engines.oauth_state import decode_oauth_state, encode_oauth_state
from login_with_haravan.engines.redirects import (
    DEFAULT_HELPDESK_REDIRECT,
    normalize_helpdesk_redirect,
)


class HaravanIdentityTest(unittest.TestCase):
    def test_normalizes_haravan_oidc_claims(self):
        profile = normalize_haravan_profile(
            {
                "sub": "200000815071",
                "email": "Owner@Example.com",
                "orgid": "200000376735",
                "orgname": "My Shop",
                "orgcat": "Clothing",
                "role": ["admin"],
                "name": "My Name",
            }
        )

        self.assertEqual(profile["userid"], "200000815071")
        self.assertEqual(profile["email"], "owner@example.com")
        self.assertEqual(profile["org_id"], "200000376735")
        self.assertEqual(profile["role"], ["admin"])

    def test_requires_user_email_and_org(self):
        with self.assertRaises(HaravanIdentityError) as ctx:
            normalize_haravan_profile({"sub": "200000815071", "email": "owner@example.com"})

        self.assertIn("orgid", str(ctx.exception))

    def test_builds_stable_link_fields(self):
        fields = build_link_fields(
            "owner@example.com",
            {
                "userid": "user-1",
                "email": "owner@example.com",
                "org_id": "org-1",
                "roles": "admin",
            },
        )

        self.assertEqual(fields["haravan_userid"], "user-1")
        self.assertEqual(fields["haravan_orgid"], "org-1")
        self.assertEqual(json.loads(fields["haravan_roles"]), ["admin"])

    def test_link_name_is_sanitized_and_bounded(self):
        name = make_link_name("org id with spaces", "u" * 180)

        self.assertLessEqual(len(name), 140)
        self.assertNotIn(" ", name)

    def test_decoder_accepts_bytes_and_strings(self):
        payload = {"access_token": "token", "expires_in": 3600}

        self.assertEqual(decode_json_payload(json.dumps(payload).encode("utf-8")), payload)
        self.assertEqual(decode_json_payload(json.dumps(payload)), payload)

    def test_oauth_state_round_trips_redirect_to(self):
        state = {
            "site": "https://haravan.help",
            "token": "abc",
            "redirect_to": "https://haravan.help/helpdesk/my-tickets/new",
        }

        self.assertEqual(decode_oauth_state(encode_oauth_state(state)), state)

    def test_normalizes_helpdesk_redirects(self):
        self.assertEqual(
            normalize_helpdesk_redirect("/helpdesk/my-tickets/new"),
            "/helpdesk/my-tickets/new",
        )
        self.assertEqual(
            normalize_helpdesk_redirect("https://haravan.help/helpdesk/my-tickets/new"),
            "/helpdesk/my-tickets/new",
        )
        self.assertEqual(
            normalize_helpdesk_redirect("https://old-domain.example/helpdesk/my-tickets?status=Open"),
            "/helpdesk/my-tickets?status=Open",
        )

    def test_rejects_missing_encoded_or_desk_redirects(self):
        self.assertEqual(normalize_helpdesk_redirect(None), "/helpdesk/my-tickets")
        self.assertEqual(normalize_helpdesk_redirect("/desk/hd-ai-settings"), DEFAULT_HELPDESK_REDIRECT)
        self.assertEqual(
            normalize_helpdesk_redirect("%2Fdesk%2Fhd-ai-settings"),
            DEFAULT_HELPDESK_REDIRECT,
        )
        self.assertEqual(normalize_helpdesk_redirect("/missing-page"), DEFAULT_HELPDESK_REDIRECT)
        self.assertEqual(normalize_helpdesk_redirect("/helpdesk/not-a-ticket-route"), DEFAULT_HELPDESK_REDIRECT)
        self.assertEqual(
            normalize_helpdesk_redirect("https://haravan.help/notfound"),
            DEFAULT_HELPDESK_REDIRECT,
        )


if __name__ == "__main__":
    unittest.main()
