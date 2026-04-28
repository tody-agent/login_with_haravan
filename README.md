# Login With Haravan

Frappe custom app for logging in to Frappe Helpdesk with a Haravan Account.

## What It Does

User flow:

```text
https://haravandesk.s.frappe.cloud/login
  -> Login with Haravan Account
  -> Haravan OAuth login
  -> Frappe callback
  -> Frappe Helpdesk logged-in session
```

The callback stores:

```text
userid  -> haravan_userid
email   -> email
orgid   -> haravan_orgid
```

Records are saved in the `Haravan Account Link` DocType. Frappe also stores the social login user id on the User document under provider `haravan_account`.

## Callback URL

Add this URL in Haravan Partner Dashboard:

```text
https://haravandesk.s.frappe.cloud/api/method/login_with_haravan.oauth.login_via_haravan
```

## Required Scopes

```text
openid profile email org userinfo
```

## Quick Local Install

```bash
cd /Volumes/Data/Frappe/frappe-bench
ln -sfn /Volumes/Data/Haravan/login_with_haravan apps/login_with_haravan
./env/bin/pip install -e apps/login_with_haravan
bench --site boxme.localhost install-app login_with_haravan
bench --site boxme.localhost set-config haravan_login '{"client_id":"HARAVAN_CLIENT_ID","client_secret":"HARAVAN_CLIENT_SECRET"}'
bench --site boxme.localhost execute login_with_haravan.setup.install.configure_haravan_social_login
bench --site boxme.localhost clear-cache
```

Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md).
