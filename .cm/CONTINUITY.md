# Continuity - Login With Haravan

## Active Goal

Productionize a standalone Frappe app that lets users log into Frappe Helpdesk with Haravan Account and stores Haravan `userid`, `email`, and `orgid`.

## Current Phase

Deployed to Frappe Cloud bench/site, validating OAuth configuration with Haravan Partner Dashboard.

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

## Next Actions

1. Confirm the Social Login Key exists and is enabled in Frappe.
2. Confirm Haravan Partner Dashboard has the exact callback URL.
3. Copy the login button link and decode `redirect_uri` if Haravan still rejects.
4. After successful login, verify `Haravan Account Link` records contain `email`, `haravan_userid`, `haravan_orgid`.
5. Use `docs/NEXT_STEPS_FOR_AGENT.md` as the production setup checklist.
