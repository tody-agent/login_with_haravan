# Project: Login With Haravan

## Summary

`login_with_haravan` is a standalone Frappe custom app for Frappe Helpdesk. It adds a custom Social Login Key provider that authenticates users through Haravan Account, then stores Haravan identity details in Frappe.

## Production Target

```text
https://haravan.help
```

Frappe Cloud site slug: `haravandesk.s.frappe.cloud`.

## App Name

```text
login_with_haravan
```

## User Flow

```text
Frappe /login
  -> Login with Haravan Account
  -> https://accounts.haravan.com/connect/authorize
  -> /api/method/login_with_haravan.oauth.login_via_haravan
  -> Frappe session created
  -> Haravan Account Link upserted
```

## Data Stored

DocType: `Haravan Account Link`

Fields:

```text
user
email
haravan_userid
haravan_orgid
haravan_orgname
haravan_orgcat
haravan_roles
raw_profile
last_login
```

## Non-Goals

- No embedded Haravan app UI.
- No Haravan order/product API access.
- No external callback service on Cloudflare, Railway, or Vercel.
- No modification of Frappe core or Helpdesk core.
