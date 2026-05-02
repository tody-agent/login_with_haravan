# Design: Haravan Account Social Login

## Context

Frappe already supports custom OAuth providers through `Social Login Key`. Haravan Account supports OAuth/OIDC endpoints on `https://accounts.haravan.com`.

The integration should run fully inside the Frappe Helpdesk site. Frappe builds the authorize URL, Haravan authenticates the user, and Haravan redirects back to a whitelisted Frappe method.

## Components

### Social Login Key

Provider:

```text
haravan_account
```

Display name:

```text
Haravan Account
```

Authorize endpoint:

```text
https://accounts.haravan.com/connect/authorize
```

Token endpoint:

```text
https://accounts.haravan.com/connect/token
```

Userinfo endpoint:

```text
https://accounts.haravan.com/connect/userinfo
```

Callback:

```text
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

### Frappe Callback

File:

```text
login_with_haravan/oauth.py
```

Responsibilities:

- Receive `code` and `state`.
- Use Frappe OAuth helper to exchange code and fetch userinfo.
- Normalize Haravan claims.
- Call Frappe login helper to create a session.
- Upsert `Haravan Account Link`.
- Log errors with `frappe.log_error()`.

### Identity Engine

File:

```text
login_with_haravan/engines/haravan_identity.py
```

Responsibilities:

- Normalize `sub`, `userid`, `user_id`, or `id` into `userid`.
- Normalize `orgid`, `org_id`, or `organization_id` into `orgid`.
- Lowercase email.
- Build stable DocType name from org/user ids.
- Build serializable DocType fields.

### Setup Helper

File:

```text
login_with_haravan/setup/install.py
```

Responsibilities:

- Create or update Social Login Key.
- Read credentials from `haravan_account_login`, then legacy `haravan_login`, then flat `haravan_client_id` / `haravan_client_secret`.
- Keep `Social Login Key.redirect_url` relative so Frappe can use the active request domain automatically.
- Resolve token exchange callback from `haravan_account_login.redirect_uri` when configured, otherwise from the request domain.
- Keep setup idempotent in `after_install` and `after_migrate`.

## Configuration

Site config:

```json
{
  "haravan_account_login": {
    "client_id": "HARAVAN_CLIENT_ID",
    "client_secret": "HARAVAN_CLIENT_SECRET"
  }
}
```

Optional fixed-domain override:

```json
{
  "haravan_account_login": {
    "client_id": "HARAVAN_CLIENT_ID",
    "client_secret": "HARAVAN_CLIENT_SECRET",
    "redirect_uri": "https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan"
  }
}
```

Haravan Partner Dashboard redirect URL must exactly match:

```text
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

## Verification

Run local verification:

```bash
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
python3 -m compileall -q login_with_haravan
python3 -m pip wheel . --no-deps -w /tmp/login_with_haravan_wheel_test
```

Run production verification:

1. Open `https://haravan.help/login`.
2. Click `Login with Haravan Account`.
3. Confirm Haravan accepts the redirect URI.
4. Complete login.
5. Confirm `Haravan Account Link` record exists.
