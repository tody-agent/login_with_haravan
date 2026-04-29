# Troubleshooting

## Haravan: `invalid_request Invalid redirect_uri`

Root cause:

Haravan rejected the authorize request before Frappe callback ran.

Check:

1. Open `https://haravandesk.s.frappe.cloud/login`.
2. Right-click `Login with Haravan Account`.
3. Copy link address.
4. Decode the `redirect_uri` parameter.
5. Confirm it exactly equals:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

Then confirm this exact URL exists in Haravan Partner Dashboard.

## Login Button Missing

Check:

- App installed on the site, not only bench.
- Social Login Key `haravan_account` exists.
- `enable_social_login` is checked.
- Client ID and Client Secret are present.
- Base URL is present.
- Clear site cache after changing Social Login Key.

## Frappe Cloud Cannot Install App

Check:

- `pyproject.toml` has `name = "login_with_haravan"`.
- `setup.py` has `name="login_with_haravan"`.
- `login_with_haravan/hooks.py` exists.
- `login_with_haravan/patches.txt` exists.
- Root `tests/` does not exist.

## No `Haravan Account Link` Created

Check Frappe Error Log for:

```text
Haravan social login failed
Haravan Account Link persistence failed
```

Possible causes:

- Haravan userinfo does not include email.
- Haravan userinfo does not include `orgid`.
- User is disabled in Frappe.
- Signup disabled while the user does not exist yet.

## Callback Returns `417: Uncaught Exception`

Check the latest Frappe Error Log titled:

```text
Haravan social login failed
```

The first JSON line includes a safe `stage` value:

```text
get_info_via_oauth
normalize_haravan_profile
login_oauth_user
```

Use that stage as the root-cause boundary. The log intentionally does not include
access tokens, refresh tokens, client secrets, or authorization codes.

You can also run this Desk method as Administrator/System Manager to verify
non-secret Social Login Key configuration:

```text
login_with_haravan.diagnostics.get_haravan_login_status
```

## Login Returns To `/desk` Instead Of Previous Helpdesk Page

Expected flow:

```text
/helpdesk/my-tickets/new
  -> /login?redirect-to=/helpdesk/my-tickets/new
  -> Login with Haravan Account
  -> /helpdesk/my-tickets/new
```

The app includes `/assets/login_with_haravan/js/haravan_login_redirect.js` on
website pages. On `/login`, it stores the `redirect-to` target in a short-lived
cookie and rewrites the Haravan OAuth `state.redirect_to` before the user leaves
for Haravan. The callback also reads this cookie as a fallback and overrides
`state.redirect_to` before calling Frappe's `login_oauth_user`.
