# Login With Haravan

Frappe custom app for logging in to Frappe Helpdesk with a Haravan Account.

## What It Does

User flow:

```text
https://haravan.help/login
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
https://haravan.help/api/method/login_with_haravan.oauth.login_via_haravan
```

By default the app keeps the Social Login Key callback path relative, so Frappe
uses the active request domain automatically. If a fixed domain is needed, set
`haravan_account_login.redirect_uri` in bench/site config; changing that value
does not require a migration.

## Required Scopes

```text
openid profile email org userinfo
```

## Quick Local Install

```bash
cd /Volumes/Data/Frappe/frappe-bench
ln -sfn /Volumes/Data/Haravan/frappe_login_with_haravan apps/login_with_haravan
./env/bin/pip install -e apps/login_with_haravan
bench --site boxme.localhost install-app login_with_haravan
bench --site boxme.localhost set-config haravan_account_login '{"client_id":"HARAVAN_CLIENT_ID","client_secret":"HARAVAN_CLIENT_SECRET"}'
bench --site boxme.localhost execute login_with_haravan.setup.install.configure_haravan_social_login
bench --site boxme.localhost clear-cache
```

Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md).

## Agent Documentation

This package includes OpenSpec and handoff docs so another AI agent can continue implementation safely:

```text
AGENTS.md
.cm/CONTINUITY.md
openspec/project.md
openspec/AGENT_HANDOFF.md
openspec/AGENT_NEXT_STEPS.md
openspec/SITE_CONFIG.md
openspec/changes/haravan-social-login/design.md
openspec/changes/haravan-social-login/tasks.md
openspec/changes/haravan-social-login/specs/social-login/spec.md
docs/architecture/oauth-flow.md
docs/guide/configuration.md
docs/guide/troubleshooting.md
```

Start with `AGENTS.md`, then `openspec/project.md`, then `.cm/CONTINUITY.md`, then `openspec/AGENT_NEXT_STEPS.md`.

## Run Tests

```bash
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
```
