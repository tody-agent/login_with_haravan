# Working Memory

- Active Goal: Bitrix metajson customer enrichment via Server Script
- Just Completed: ✅ Reworked Option A away from custom app runtime into a
  Desk-managed Server Script deploy helper; quality gate passed with pre-commit
  plus 100 Python tests, 0 failures.
- Next Actions:
  - Run `scripts/deploy_bitrix_metajson_enrichment.py` with Haravan Helpdesk
    API credentials to create/update the Server Script and guard Custom Fields.
  - Wire production metajson/Server Script to call API method
    `haravan_bitrix_metajson_company_enrichment`.
  - Smoke test with an orgid that exists in Bitrix and confirm `HD Customer Data`
    snapshot plus guard fields.
- Current Phase: verified
- Working Context: Runtime logic lives in `Server Script` source embedded in
  `scripts/deploy_bitrix_metajson_enrichment.py`, not in custom app Python. It
  uses `bitrix_refresh_ttl_minutes`, cache lock by `orgid`,
  `custom_bitrix_last_checked_at`, and Bitrix `DATE_MODIFY` to avoid loops and
  repeated writes.

- Previous Goal: CC Email Smoke Test on haravan.help completed
- Just Completed: Ticket CC Emails Option B implemented and production smoke-tested on `0.1.6`
  in commit `8be5a14`. Added `custom_cc_emails`
  setup for `HD Ticket`, Default template row, pure CC normalization/merge engine,
  `HD Ticket` validation hook, and `HDTicketCCMixin` for agent reply and acknowledgement
  CC delivery.
- Quality Gate: `npm run test` passed with pre-commit lint and 84 Python tests.
  `python3 -m compileall -q login_with_haravan` and `python3 -m pip wheel . --no-deps`
  also passed; temporary build artifacts were removed.
- Next Actions:
  - Keep temporary production Server Script `HD Ticket - CC Created Notification`
    disabled while `login_with_haravan >= 0.1.6` is deployed, to avoid duplicate
    CC created-ticket emails.
  - If the production Desk custom button remains in use, update `Onboarding - Agent Ticket Dialog`
    and `haravan_agent_create_customer_ticket` to collect/pass `custom_cc_emails`.
  - Deploy `scripts/fix_ai_assist_and_analyze_comment.py` to the live Helpdesk site when ready.
  - Smoke test `AI - Ticket Assist Menu` on a real HD Ticket with Vietnamese content.
  - Decide later whether AI drafts should stay as internal comments or fill/send the public reply composer.
- Current Phase: ticket CC source hook verified on production; PR #5 remains open for local operations/docs merge
- Working Context: AI Reply Copilot upgrade is documented in `openspec/changes/ai-reply-copilot-upgrade/`. The patch keeps existing Desk script endpoints stable, adds up to 3 ranked reply options, auto-selects the highest-confidence option, uses richer ticket/recent-message context, and enforces Vietnamese with accents. Local `./test_gate.sh` passed after adding regression tests.

- What Failed: Bulk-deleted inactive Desk scripts when the user asked to rewrite/refactor them.
- Why It Failed: Interpreted "xóa code rác" too broadly and treated inactive records as removable inventory instead of legacy code to rewrite.
- How to Prevent: For production Desk-managed scripts, export first, then update/refactor records in place. Do not delete records unless the user explicitly approves deletion after seeing the rewrite inventory.
- Scope: site:haravandesk.s.frappe.cloud scripts

## Mistakes & Learnings

- [Decision]: Merge security-only fixes from open Sentinel branches by porting the
  exact behavior into the active integration branch, then proving with local tests
  instead of blindly merging duplicate branches. — scope: module:customer-profile-oauth-security

- What Failed: `refresh_customer_profile` could load arbitrary `HD Customer` and
  `Contact` documents from direct whitelisted arguments before checking document
  permissions.
- How to Prevent: For every direct whitelisted profile/detail API, call
  `frappe.has_permission(..., throw=True)` on user-controlled DocType names before
  `frappe.get_doc`, and add denial-path unit tests.
- Scope: module:customer-profile-bitrix-sync

- What Failed: Customer portal ticket `49679` opened with a blank middle
  activity area showing only the `Activity` heading, even though
  `HD Ticket.description` contained `<p>Góp ý </p>`.
- Why It Failed: The Helpdesk customer ticket view renders only linked
  `Communication` rows in `TicketConversation.vue`; `HD Ticket.description` is
  not rendered directly. The ticket had no linked `Communication` because a
  stale cached `Communication - Notify Ticket CC on Reply` Server Script still
  used helper functions and raised `name 'as_text' is not defined` during
  `Communication.after_insert`.
- How to Prevent: For blank customer portal Activity screens, query
  `Communication` by `reference_doctype="HD Ticket"` and `reference_name`
  before changing frontend code. If Error Log points at a stale Server Script
  body, save/nudge the Server Script to flush cache, then backfill only the
  affected ticket's first `Communication` from `HD Ticket.description`.
- Scope: site:haravandesk.s.frappe.cloud scripts

- What Failed: Ticket `61117` had `custom_orgid=1000391653`, Bitrix/profile
  routing completed, but `HD Ticket.customer` stayed empty and no `HD Customer`
  or `HD Customer Data` existed for the org.
- Why It Failed: The production ticket profile/routing path enriched ticket cache
  fields but did not invoke the `haravan_bitrix_metajson_company_enrichment`
  API that creates the `HD Customer`, stores the Bitrix snapshot, and links the
  ticket.
- How to Prevent: When a ticket has profile/routing data but no customer, call
  `haravan_bitrix_metajson_company_enrichment` with `orgid`, `ticket`, and
  `force=1`; for a durable fix, wire the ticket/profile workflow to call that
  endpoint after resolving `custom_orgid`.
- Scope: site:haravandesk.s.frappe.cloud scripts

- What Failed: Customer Profile modal showed a matched Bitrix company, but
  pressing "Đồng bộ" returned `Ticket has no Haravan Company ID` on ticket
  `61111`.
- Why It Failed: The profile API built a broad candidate/fallback set and
  matched Bitrix company `200000239589`, while the sync API only read Haravan
  ID fields directly from `HD Ticket`; `HD Ticket.custom_orgid` was blank, so
  the sync action rejected a profile that had already matched.
- How to Prevent: When a UI action follows a successful profile lookup, pass
  the resolved `company.company_id` to the sync API and let the API prefer
  request-level `company_id/orgid` before ticket fields. Keep profile and sync
  lookup sources aligned with regression tests.
- Scope: module:customer-profile-bitrix-sync

- What Failed: `AI - Ticket Copilot Event` spammed Error Logs with
  `name 'as_text' is not defined` on every `HD Ticket.after_insert`.
- Why It Failed: Production Server Script used helper functions where one helper
  called another (`choose_ai_config()` -> `as_text()`). On this Frappe safe_exec
  runtime, script globals/locals are split, so nested helper lookups can miss
  symbols defined in the same Server Script.
- How to Prevent: Keep production Server Scripts top-level or move reusable logic
  into source-controlled app code. Avoid nested helper-function dependencies in
  Server Scripts; add a last-resort guard so AI/enrichment never blocks ticket creation.
- Scope: site:haravandesk.s.frappe.cloud scripts

- What Failed: Portal ticket intake still blocked creation after the syntax fix
  when `custom_contact_phone` or `custom_store_url` was blank.
- Why It Failed: Enrichment/supporting fields were enforced as hard gates in both
  production Server Scripts and `HD Ticket` Custom Field metadata (`reqd=1`), even
  though Haravan users may manage multiple orgs or have incomplete org/contact data.
- How to Prevent: Treat Helpdesk intake enrichment as best-effort. Store URL,
  product suggestion, phone normalization, OrgID, MyHaravan, and HD Customer mapping
  should enrich when present but never block ticket creation; agents can complete
  missing data after the ticket exists.
- Scope: site:haravandesk.s.frappe.cloud scripts

- What Failed: Creating an `HD Ticket` through `helpdesk.helpdesk.doctype.hd_ticket.api.new`
  returned only `{"exc_type":"SyntaxError"}` and blocked portal ticket creation.
- Why It Failed: Production Server Script `Ticket - Store URL Enrich` was saved with
  two leading spaces on every top-level line, so RestrictedPython raised
  `IndentationError: unexpected indent` at `SCRIPT_TITLE = "HD Ticket - Haravan Store URL Enrichment"`
  during the `HD Ticket.before_validate` event.
- How to Prevent: For production Server Scripts, verify the stored source starts at
  column 0 for top-level statements before enabling, and check recent Error Logs for
  the concrete `<serverscript>: ...` filename before changing app code.
- Scope: site:haravandesk.s.frappe.cloud scripts

- What Failed: CC email for agent-created ticket was stored on `HD Ticket.custom_cc_emails`
  but no `Email Queue` or `Error Log` was created.
- Why It Failed: Production was still running `login_with_haravan` `0.1.5`; the
  `after_insert` CC notification hook was shipped in `0.1.6` but not deployed/migrated.
  Ticket `51710` also predated the production Server Script hotfix, so it required a
  one-time manual queue.
- How to Prevent: For production hotfixes, verify live app version before testing,
  and confirm the data path creates an `Email Queue` record for the ticket reference.
  Keep temporary Server Scripts disabled once the source-controlled app hook is deployed.
- Scope: module:ticket-cc-emails

- What Worked: Browser smoke test created `HD Ticket 52407` from
  `https://haravan.help/helpdesk/tickets/new` with `raised_by=sociads@gmail.com`
  and `custom_cc_emails=hai.minh@outlook.com`; source-controlled app `0.1.6`
  queued `Email Queue f2ssh8b9vh`, status `Sent`, to the CC recipient.
- Why It Worked: Production had been upgraded to `login_with_haravan 0.1.6`,
  so the app After Insert hook handled the created-ticket CC notification. The
  temporary `HD Ticket - CC Created Notification` Server Script was disabled to
  prevent duplicate emails.
- How to Prevent Regressions: For every CC smoke test, check ticket persistence,
  `Email Queue.recipients`, and recent Error Logs. Do not count UI success alone
  as a pass.
- Scope: module:ticket-cc-emails

- What Failed: AI reply suggestion dialog showed weak/empty drafts and Vietnamese UI/prompt copy without accents.
- Why It Failed: `generate-ai-reply` only sent sparse ticket context and a loose single-option schema, while the dialog always opened one textarea instead of exposing multiple plausible ticket situations.
- How to Prevent: For Helpdesk AI scripts, include ticket fields plus recent exchanges in chronological order, require a bounded JSON schema with up to 3 ranked options, auto-select by confidence, and add regression tests for accented Vietnamese UI/prompt copy.
- Scope: module:helpdesk-ai-scripts

- What Failed: Opening Helpdesk ticket pages showed `Internal Server Error`; `frappe.client.get_list` for `HD Agent` with field `user.user_image` generated SQL using missing alias `tabUser.name`.
- Why It Failed: Production was still running `login_with_haravan` `0.1.3`, while the local fix commit bumped `pyproject.toml`, `setup.py`, and `hooks.py` to `0.1.4` but left package `__version__` at `0.1.3`, so the Frappe Cloud installed app version did not reflect the patch reliably.
- How to Prevent: Keep `login_with_haravan.__version__`, `pyproject.toml`, `setup.py`, and `hooks.py` versions identical; test metadata consistency before shipping Frappe Cloud hotfixes.
- Scope: module:login_with_haravan packaging

- What Failed: Haravan OAuth returned `invalid_request Invalid redirect_uri` after Frappe Cloud primary domain changed to `haravan.help`.
- Why It Failed: Frappe generated `redirect_uri` from the active/request domain while the app's token exchange and docs did not share one configurable callback source; Haravan requires the authorize and token `redirect_uri` values to match the Partner Dashboard exactly.
- How to Prevent: Keep Social Login Key callback relative for automatic request-domain behavior. Use exact `haravan_account_login.redirect_uri` in Site Config only when a fixed-domain override is needed without migrate/setup.
- Scope: module:login_with_haravan.oauth

- What Failed: `bench migrate` crashed with `ModuleNotFoundError: No module named 'login_with_haravan.frappe_x_haravan'` after renaming the display title in modules.txt.
- Why It Failed: `modules.txt` was changed from `Login With Haravan` to `Login With Haravan` in commit af7665c. Frappe's `sync_for()` scrubs module names via `frappe.scrub()`: `"Login With Haravan"` → `"frappe_x_haravan"`. But the actual Python directory is `login_with_haravan/login_with_haravan/` → scrubbed as `"login_with_haravan"`. The import `login_with_haravan.frappe_x_haravan` doesn't exist.
- How to Prevent: **NEVER rename `modules.txt` unless you also rename the corresponding Python directory.** The value in `modules.txt` MUST scrub (via `frappe.scrub()`) to the actual directory name. Furthermore, the `"module"` field inside any custom DocType's JSON schema file must exactly match the original string (e.g., `"Login With Haravan"`) so that Frappe's `sync_all()` loads the correct scrubbed Python module. Use `hooks.py → app_title` for display branding instead.
- Scope: global (Frappe app development)

- What Failed: Haravan OAuth login for `sociads@gmail.com` succeeded on production
  with `User.social_logins.provider=haravan_account`, but no `Haravan Account Link`,
  `HD Customer`, or `Contact` existed for org `1000008079`.
- Why It Failed: The post-login persistence path depended on `frappe.session.user`
  after `login_oauth_user()`. In the callback context this can still be unavailable
  or `Guest`, causing `_persist_after_login()` to return silently before syncing
  Helpdesk identity records. Role matching was also too exact for mixed-case or
  multi-value role strings.
- How to Prevent: Pass the normalized profile email explicitly into post-login
  persistence, fall back to that email if the callback session user is empty, and
  normalize Haravan roles to lowercase tokens before checking owner/admin access.
- Scope: module:login_with_haravan.oauth
