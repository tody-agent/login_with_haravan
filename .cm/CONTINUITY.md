# Continuity - Login With Haravan

## Active Goal

Personalize the Helpdesk new-ticket form so agents only enter `Link Web / MyHaravan` and `Product Suggestion`, while customer/org/product metadata is resolved automatically.

## Current Phase

Planning ticket autofill implementation.

## Known Production Site

```text
https://haravandesk.s.frappe.cloud
```

## GitHub Repo

```text
https://github.com/tody-agent/login_with_haravan
```

Latest known version/tag:

```text
0.1.1 / v0.1.1
```

## Key Decisions

- Use Frappe Social Login Key with provider `haravan_account`.
- Keep the callback inside Frappe, no Cloudflare/Railway service needed.
- Store Haravan identity in custom DocType `Haravan Account Link`.
- Keep pure claim normalization in `login_with_haravan/engines/haravan_identity.py`.
- Keep Frappe DB writes in `login_with_haravan/oauth.py`.
- Enforce solo vibe coding workflow: always work in feature branches and use `npm run ship` (or `./ship.sh`) to automatically push, merge to `main`, and push `main` safely.

## Mistakes & Learnings

- What Failed: Frappe Cloud said app was invalid and looked for `tests/tests/hooks.py`.
  Why It Failed: Root-level `tests` made Frappe Cloud detect the wrong package.
  How to Prevent: Keep tests under `login_with_haravan/tests/`.
  Scope: project-wide Frappe Cloud packaging.

- What Failed: Frappe Cloud said imported module `login-with-haravan` was not found.
  Why It Failed: Python package metadata used hyphenated distribution name while Frappe imports module names literally.
  How to Prevent: Use `login_with_haravan` for app name, package metadata, and module import names.
  Scope: project-wide Frappe Cloud packaging.

- What Failed: Haravan returned `invalid_request Invalid redirect_uri`.
  Why It Failed: Haravan rejects OAuth before callback when Partner Dashboard redirect URL does not exactly match Frappe's generated `redirect_uri`.
  How to Prevent: Register exact callback URL in Haravan Partner Dashboard and confirm the copied login link's `redirect_uri`.
  Scope: OAuth configuration.

- What Failed: Haravan callback surfaced as `417: Uncaught Exception` without enough production detail.
  Why It Failed: Callback logging only wrote a generic traceback after several OAuth boundaries, and the token response decoder was not robust for both `bytes` and `str` payloads.
  How to Prevent: Log a safe OAuth `stage` before re-raising callback exceptions and keep token/userinfo parsing helpers in pure engine modules with standalone tests.
  Scope: module:login_with_haravan.oauth.

- What Failed: After Login with Haravan, users could be sent to `/desk` instead of the Helpdesk page they originally opened.
  Why It Failed: Frappe social login redirects only to `state.redirect_to`; if `/login` loses or defaults the `redirect-to` query, the OAuth state defaults to Desk.
  How to Prevent: Preserve same-origin Helpdesk redirect targets on `/login` and override Haravan callback state from a short-lived cookie before calling `login_oauth_user`.
  Scope: module:login_with_haravan.oauth.

- What Failed: First-time Haravan login sent a new Website User to `/%2Fdesk%2Fhd-ai-settings` and showed `Not Permitted`.
  Why It Failed: Missing or invalid Haravan OAuth `state.redirect_to` let Frappe fall back to the Desk default app route `/desk/hd-ai-settings`, which Website Users cannot access.
  How to Prevent: Normalize Haravan callback redirects to clear `/helpdesk/my-tickets...` targets and fall back to `/helpdesk/my-tickets` on the current site domain when the state is missing, encoded, stale, or points to Desk/unknown pages.
  Scope: module:login_with_haravan.oauth.

- What Failed: GitHub Actions failed importing `login_with_haravan.engines.haravan_api` with `ModuleNotFoundError: No module named 'requests'`.
  Why It Failed: The app used `requests` for Haravan API calls, but package metadata and the test gate still declared no Python dependencies, so clean CI environments did not install it before source tests imported the module.
  How to Prevent: Declare runtime HTTP client dependencies in `requirements.txt`, `pyproject.toml`, and `setup.py`, and keep `test_gate.sh` installing `requirements.txt` before import-based tests.
  Scope: project-wide Python dependency metadata.

## Next Actions

1. Add HD Ticket custom-field metadata setup.
2. Add ticket autofill engine and whitelisted API.
3. Add Helpdesk SPA script and focused tests.
