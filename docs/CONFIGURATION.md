# Configuration

## Frappe Site Config

Use Frappe Cloud Site Config > Add Config > Custom Key.

Config name:

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

## Social Login Key

DocType:

```text
Social Login Key
```

Expected values:

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

## Haravan Partner Dashboard

Allowed redirect URL:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

Client ID and Client Secret must belong to the same Haravan app that contains this redirect URL.
