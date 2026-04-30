# Working Memory

- Active Goal: Domain-aware Haravan OAuth configuration
- Next Actions:
  - Verify production authorize URL on `https://haravan.help/login`
  - If auto-domain is not enough, set `haravan_account_login.redirect_uri` in Site Config
  - Keep Haravan Partner Dashboard redirect URL matched exactly
- Current Phase: implementation verified
- Working Context: Social Login Key should keep a relative callback path. Runtime domain is automatic from request host; exact fixed-domain override belongs in bench/site config, not a migration.

## Mistakes & Learnings

- What Failed: Haravan OAuth returned `invalid_request Invalid redirect_uri` after Frappe Cloud primary domain changed to `haravan.help`.
- Why It Failed: Frappe generated `redirect_uri` from the active/request domain while the app's token exchange and docs did not share one configurable callback source; Haravan requires the authorize and token `redirect_uri` values to match the Partner Dashboard exactly.
- How to Prevent: Keep Social Login Key callback relative for automatic request-domain behavior. Use exact `haravan_account_login.redirect_uri` in Site Config only when a fixed-domain override is needed without migrate/setup.
- Scope: module:login_with_haravan.oauth
