# Deployment Guide

## 1. Haravan Partner Dashboard

Create a Haravan public app or update the existing app.

Allowed Redirect URL:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

Required login scopes:

```text
openid profile email org userinfo
```

For this login-only integration, do not add `grant_service`, `offline_access`, commerce scopes, or webhook scopes unless another feature also needs Haravan API access after login.

## 2. Local Bench Install

```bash
cd /Volumes/Data/Frappe/frappe-bench

ln -sfn /Volumes/Data/Haravan/login_with_haravan apps/login_with_haravan
./env/bin/pip install -e apps/login_with_haravan

bench --site boxme.localhost install-app login_with_haravan
bench --site boxme.localhost migrate
```

Configure Haravan credentials:

```bash
bench --site boxme.localhost set-config haravan_login '{"client_id":"HARAVAN_CLIENT_ID","client_secret":"HARAVAN_CLIENT_SECRET"}'
bench --site boxme.localhost execute login_with_haravan.setup.install.configure_haravan_social_login
bench --site boxme.localhost clear-cache
```

Then open:

```text
http://boxme.localhost:8000/login
```

## 3. Frappe Cloud Deploy

1. Push `/Volumes/Data/Haravan/login_with_haravan` to a Git repository.
2. In Frappe Cloud, add that repository as a custom app.
3. Add the app to the bench that hosts `haravandesk.s.frappe.cloud`.
4. Install `login_with_haravan` on the `haravandesk.s.frappe.cloud` site.
5. Set site config values for Haravan Client ID and Client Secret.
6. Run the setup method once, then clear cache.

Expected callback path:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

## 4. Manual Social Login Key Values

If you configure through Frappe UI:

```text
Integrations > Authentication > Social Login Key
```

Use:

```text
Social Login Provider: Custom
Provider Name: Haravan Account
Enable Social Login: checked
Client ID: HARAVAN_CLIENT_ID
Client Secret: HARAVAN_CLIENT_SECRET
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

1. Go to `https://haravandesk.s.frappe.cloud/login`.
2. Click `Login with Haravan Account`.
3. Complete Haravan login.
4. Confirm Frappe redirects after login.
5. In Desk, open `Haravan Account Link`.
6. Confirm `email`, `haravan_userid`, and `haravan_orgid` were saved.

If the button is missing, check:

```text
Social Login Key > Haravan Account > Enable Social Login
Client ID is set
Client Secret is set
Base URL is set
```

If login returns but the account link is missing, check Error Log entries named:

```text
Haravan social login failed
Haravan Account Link persistence failed
```
