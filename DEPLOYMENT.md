# Deployment Guide

## 1. Haravan Partner Dashboard

Create a Haravan public app or update the existing app.

Allowed Redirect URL:

```text
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

Required login scopes:

```text
openid profile email org userinfo
```

For this login-only integration, do not add `grant_service`, `offline_access`, commerce scopes, or webhook scopes unless another feature also needs Haravan API access after login.

See also:

```text
docs/guide/getting-started.md
docs/guide/troubleshooting.md
```

## 2. Local Bench Install

```bash
cd /Volumes/Data/Frappe/frappe-bench

ln -sfn /Volumes/Data/Haravan/frappe_login_with_haravan apps/login_with_haravan
./env/bin/pip install -e apps/login_with_haravan

bench --site boxme.localhost install-app login_with_haravan
bench --site boxme.localhost migrate
```

Configure Haravan credentials:

```bash
# IMPORTANT: The config key MUST be "haravan_account_login" (matches Frappe core convention: {provider}_login)
bench --site boxme.localhost set-config haravan_account_login '{"client_id":"HARAVAN_CLIENT_ID","client_secret":"HARAVAN_CLIENT_SECRET"}'
bench --site boxme.localhost execute login_with_haravan.setup.install.configure_haravan_social_login
bench --site boxme.localhost clear-cache
```

> **Note:** The older key name `haravan_login` is also accepted for backward compatibility,
> but `haravan_account_login` is preferred because Frappe's built-in `get_oauth_keys()`
> looks up `f"{provider}_login"` at runtime (provider = `haravan_account`).

Then open:

```text
http://boxme.localhost:8000/login
```

## 3. Frappe Cloud Deploy

1. Push `/Volumes/Data/Haravan/frappe_login_with_haravan` to a Git repository.
2. In Frappe Cloud, add that repository as a custom app.
3. Add the app to the bench that hosts `haravandesk.s.frappe.cloud`.
4. Install `login_with_haravan` on the `haravandesk.s.frappe.cloud` site.
5. Set site config values for Haravan Client ID and Client Secret.
6. Run the setup method once, then clear cache.

Expected public callback URL when opening the site on `haravan.help`:

```text
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

By default the callback domain is automatic because the Social Login Key stores
only the relative callback path. If you need to force a specific domain without
running migrate/setup, update `haravan_account_login.redirect_uri` in Site
Config and make the Haravan Partner Dashboard redirect URL match exactly.

## 4. Manual Social Login Key Values

If you configure through Frappe UI:

```text
Integrations > Authentication > Social Login Key
```

Use:

```text
Social Login Provider: Custom
Provider Name: Login With Haravan
Enable Social Login: checked
Client ID: HARAVAN_CLIENT_ID
Client Secret: leave blank if haravan_account_login contains client_secret
Base URL: https://accounts.haravan.com
Authorize URL: /connect/authorize
Access Token URL: /connect/token
Redirect URL: /api/method/login_with_haravan.oauth.login_via_haravan
API Endpoint: /connect/userinfo
User ID Property: sub
Sign ups: Allow
```

Auth URL Data:

```json
{
  "response_mode": "query",
  "response_type": "code",
  "scope": "openid profile email org userinfo"
}
```

## 5. Verify

1. Go to `https://haravan.help/login`.
2. Click `Login With Haravan`.
3. Complete Haravan login.
4. Confirm Frappe redirects after login.
5. In Desk, open `Haravan Account Link`.
6. Confirm `email`, `haravan_userid`, and `haravan_orgid` were saved.

If the button is missing, check:

```text
Social Login Key > Haravan Account > Enable Social Login
Client ID is set
Site Config `haravan_account_login.client_secret` is set
Base URL is set
```

If login returns but the account link is missing, check Error Log entries named:

```text
Haravan social login failed
Haravan Account Link persistence failed
```

## Frappe Cloud App Validation

This repository follows the standard Frappe app layout:

```text
login_with_haravan/
  hooks.py
  modules.txt
  patches.txt
```

If Frappe Cloud still says `Not a valid Frappe App`, click the refresh icon on the Apps tab or remove and add the GitHub app again after the latest commit is visible on GitHub.

The Python package metadata also uses the Frappe app module name:

```text
project.name = login_with_haravan
setup(name="login_with_haravan")
```

Do not change those values to `login-with-haravan`; Frappe Cloud may try to import the metadata name as a Python module.
