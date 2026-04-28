# Next Steps For Agent

This document is the operating checklist for the next agent or human operator. The user has not created/configured a Haravan app before, so do not assume Partner Dashboard setup is complete.

## Current Situation

- Frappe app source exists and has been deployed/installed at least once.
- Production target site:

```text
https://haravandesk.s.frappe.cloud
```

- GitHub repo:

```text
https://github.com/tody-agent/login_with_haravan
```

- Known active issue:

```text
Haravan returns invalid_request / Invalid redirect_uri
```

This error occurs on `accounts.haravan.com` before the Frappe callback is called. Treat it as a Haravan Partner App redirect URL configuration issue until proven otherwise.

## Required Values

### Frappe callback URL

Register this exact URL in Haravan Partner Dashboard:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

Rules:

- Must be `https`.
- Must use `haravandesk.s.frappe.cloud`.
- Must not have a trailing slash.
- Must not be URL-encoded when pasted into the Partner Dashboard field.
- Must belong to the same Haravan app as the Client ID and Client Secret configured in Frappe.

### Haravan OAuth scopes

Use:

```text
openid profile email org userinfo
```

Do not add commerce scopes, webhooks, `grant_service`, or `offline_access` for this login-only flow unless a new product requirement asks for backend Haravan API access.

### Frappe Site Config

Frappe Cloud > Site > Site Config > Add Config > Custom Key:

Config Name:

```text
haravan_login
```

Value:

```json
{
  "client_id": "HARAVAN_CLIENT_ID",
  "client_secret": "HARAVAN_CLIENT_SECRET"
}
```

The values must come from the Haravan Partner App that contains the callback URL above.

## Step 1: Configure Haravan Partner App

Goal: create or update the OAuth app inside Haravan so it accepts Frappe's callback URL.

Checklist for the operator:

- [ ] Open Haravan Partner Dashboard.
- [ ] Create a public/OAuth app or open the existing app used for this integration.
- [ ] Find OAuth / Login / App URLs / Redirect URLs settings.
- [ ] Add this callback:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

- [ ] Configure login scopes:

```text
openid profile email org userinfo
```

- [ ] Save the app.
- [ ] Copy Client ID.
- [ ] Copy Client Secret.

Agent action:

- Ask the user to paste or confirm the Client ID and Client Secret are from this same Haravan app.
- Do not ask the user to paste secrets into chat unless necessary. Prefer telling them exactly where to put secrets in Frappe Cloud.

## Step 2: Confirm Frappe App Installed On Site

Goal: make sure `login_with_haravan` is installed on the site, not only added to the bench.

Checklist:

- [ ] In Frappe Cloud, open site `haravandesk.s.frappe.cloud`.
- [ ] Go to Apps tab.
- [ ] Confirm `Login With Haravan` or `login_with_haravan` appears in installed site apps.

If missing:

- Install app from Site > Apps > Install App.
- If the app does not appear in install list, go to Bench > Apps and confirm it was deployed to the bench.

Agent action:

- If install fails, inspect the exact Frappe Cloud deploy/install error first.
- Do not modify OAuth code until app install issues are solved.

## Step 3: Configure Frappe Site Config

Goal: give Frappe the Haravan Client ID and Client Secret.

In Frappe Cloud:

1. Open site `haravandesk.s.frappe.cloud`.
2. Go to Site Config.
3. Add Config.
4. Select `Custom Key`.
5. Use Config Name:

```text
haravan_login
```

6. Use Value:

```json
{
  "client_id": "HARAVAN_CLIENT_ID",
  "client_secret": "HARAVAN_CLIENT_SECRET"
}
```

7. Save.

Agent action:

- Confirm JSON is valid.
- Confirm the key is exactly `haravan_login`, not `haravan_client_id`.
- If Frappe Cloud UI cannot store JSON objects, use two Custom Keys instead:

```text
haravan_client_id = HARAVAN_CLIENT_ID
haravan_client_secret = HARAVAN_CLIENT_SECRET
```

The app supports both formats.

## Step 4: Create Or Update Social Login Key

Goal: create Frappe's OAuth provider row for Haravan.

Preferred method:

- Run or trigger:

```text
login_with_haravan.setup.install.configure_haravan_social_login
```

If Frappe Cloud does not expose method execution, configure manually in Desk:

1. Visit site and log in as Administrator/System Manager.
2. Search `Social Login Key`.
3. Create or open `Haravan Account`.
4. Set:

```text
Social Login Provider: Custom
Provider Name: Haravan Account
Enable Social Login: checked
Client ID: HARAVAN_CLIENT_ID
Client Secret: HARAVAN_CLIENT_SECRET
Base URL: https://accounts.haravan.com
Custom Base URL: checked
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

Then save and clear cache.

Agent action:

- Confirm the Social Login Key document name is likely `haravan_account`. Frappe auto-scrubs `Provider Name`.
- Confirm `enable_social_login` is checked.
- Confirm client secret is saved. Frappe login page hides providers without a usable secret.

## Step 5: Validate Generated Login URL

Goal: prove what Frappe sends to Haravan before touching code.

Manual browser check:

1. Open:

```text
https://haravandesk.s.frappe.cloud/login
```

2. Right-click `Login with Haravan Account`.
3. Copy link address.
4. Decode the `redirect_uri` query parameter.
5. It must equal:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

Interpretation:

- If `redirect_uri` is different, fix Frappe Social Login Key or site URL configuration.
- If `redirect_uri` is correct but Haravan rejects it, fix Haravan Partner Dashboard redirect URL.
- If Haravan accepts and redirects back to Frappe, then move to callback/userinfo debugging.

Agent action:

- Ask for the copied login URL if the user cannot decode it.
- Do not ask for Client Secret when debugging redirect URI; it is not needed.

## Step 6: End-To-End Login Test

Goal: verify actual user login and identity persistence.

Steps:

1. Open:

```text
https://haravandesk.s.frappe.cloud/login
```

2. Click `Login with Haravan Account`.
3. Complete Haravan login and organization selection.
4. Confirm browser returns to Frappe.
5. Confirm user is logged in.
6. In Frappe Desk, search:

```text
Haravan Account Link
```

7. Confirm a record exists with:

```text
email
haravan_userid
haravan_orgid
last_login
```

Agent action:

- If login succeeds but no link exists, inspect Frappe Error Log.
- If callback fails after returning from Haravan, inspect errors titled:

```text
Haravan social login failed
Haravan Account Link persistence failed
```

## Step 7: Optional Diagnostic Code For Agent

Only add code if configuration cannot be verified manually.

Useful diagnostic endpoint:

```text
login_with_haravan.diagnostics.get_haravan_login_status
```

It should return non-secret status:

```json
{
  "provider_exists": true,
  "enabled": true,
  "provider_name": "Haravan Account",
  "base_url": "https://accounts.haravan.com",
  "redirect_url": "/api/method/login_with_haravan.oauth.login_via_haravan",
  "full_redirect_url": "https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan",
  "has_client_id": true,
  "has_client_secret": true,
  "auth_url_data": {
    "response_mode": "query",
    "response_type": "code",
    "scope": "openid profile email org userinfo"
  }
}
```

Never return Client Secret.

## Decision Tree

### Error: `Invalid redirect_uri`

Cause:

Haravan Partner Dashboard does not accept Frappe's `redirect_uri`.

Next action:

- Decode login URL.
- Compare redirect URL exactly.
- Fix Haravan Partner Dashboard or Frappe Social Login Key.

### Login button missing

Cause:

Frappe provider hidden due to missing/disabled Social Login Key or missing secret.

Next action:

- Check Social Login Key.
- Clear cache.

### Callback returns Frappe error page

Cause:

Now code may be running. Inspect Error Log.

Next action:

- Check `Haravan social login failed`.
- Check token exchange/userinfo response.
- Check required fields: `email`, `sub/userid`, `orgid`.

### User logs in but no org link

Cause:

Login works, persistence failed.

Next action:

- Check `Haravan Account Link persistence failed`.
- Confirm DocType exists.
- Confirm required fields are present in normalized profile.

## Completion Criteria

The integration is complete when:

- [ ] Haravan Partner App has exact redirect URL.
- [ ] Frappe Site Config contains correct Haravan credentials.
- [ ] Social Login Key is enabled and visible on login page.
- [ ] Haravan accepts OAuth authorize request.
- [ ] User returns to Frappe and is logged in.
- [ ] `Haravan Account Link` is created/updated with `email`, `haravan_userid`, `haravan_orgid`.
- [ ] Troubleshooting notes are updated with any new production-specific findings.
