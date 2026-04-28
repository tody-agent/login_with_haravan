# AGENTS.md - Login With Haravan

## Project Purpose

This repository is a standalone Frappe custom app that adds "Login with Haravan Account" to Frappe Helpdesk.

Primary production site:

```text
https://haravandesk.s.frappe.cloud
```

Current GitHub source repository:

```text
https://github.com/tody-agent/login_with_haravan
```

## Architecture Rules

Follow the Frappe 7-layer style used here:

1. DocType schema lives under `login_with_haravan/login_with_haravan/doctype/`.
2. Pure mapping/business logic lives under `login_with_haravan/engines/`.
3. Whitelisted callback/API code lives in `login_with_haravan/oauth.py`.
4. Install/migrate setup lives in `login_with_haravan/setup/install.py`.
5. Tests live in `login_with_haravan/tests/`.

Do not modify Frappe core or Helpdesk core for this integration.

## Important Implementation Details

- Frappe app/module name must stay `login_with_haravan`.
- Python package metadata must also use `login_with_haravan`, not `login-with-haravan`.
- Provider DocType name is `haravan_account`.
- Provider display name is `Haravan Account`.
- OAuth callback endpoint is:

```text
/api/method/login_with_haravan.oauth.login_via_haravan
```

- Full production callback URL is:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

## Common Failure Modes

### Frappe Cloud says app is invalid

Check that the app package contains:

```text
login_with_haravan/hooks.py
login_with_haravan/modules.txt
login_with_haravan/patches.txt
```

Also keep tests inside `login_with_haravan/tests/`, not root `tests/`, because Frappe Cloud may detect root `tests` as an app.

### Frappe Cloud says imported module `login-with-haravan` not found

Keep these exact values:

```text
pyproject.toml: name = "login_with_haravan"
setup.py: name="login_with_haravan"
```

### Haravan says `invalid_request Invalid redirect_uri`

This is Haravan Partner Dashboard configuration, not the callback code. The redirect URL registered in Haravan must exactly match:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

## Verification Commands

Run from repo root:

```bash
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
python3 -m compileall -q login_with_haravan
python3 -m pip wheel . --no-deps -w /tmp/login_with_haravan_wheel_test
```

Remove temporary artifacts before committing:

```bash
rm -rf build dist *.egg-info /tmp/login_with_haravan_wheel_test
find . -type d -name __pycache__ -prune -exec rm -rf {} +
```

## Next Deployment/Configuration Work

Read this file before continuing production setup:

```text
docs/NEXT_STEPS_FOR_AGENT.md
```
