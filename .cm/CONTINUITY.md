# Working Memory

- Active Goal: AI Reply Copilot Upgrade
- Just Completed: Ticket CC Emails Option B implemented and shipped as `0.1.5`
  in commit `8be5a14`. Added `custom_cc_emails`
  setup for `HD Ticket`, Default template row, pure CC normalization/merge engine,
  `HD Ticket` validation hook, and `HDTicketCCMixin` for agent reply and acknowledgement
  CC delivery.
- Quality Gate: `npm run test` passed with pre-commit lint and 84 Python tests.
  `python3 -m compileall -q login_with_haravan` and `python3 -m pip wheel . --no-deps`
  also passed; temporary build artifacts were removed.
- Next Actions:
  - Deploy/migrate `login_with_haravan` so `after_migrate` creates `custom_cc_emails`
    and loads the `HD Ticket` mixin.
  - If the production Desk custom button remains in use, update `Onboarding - Agent Ticket Dialog`
    and `haravan_agent_create_customer_ticket` to collect/pass `custom_cc_emails`.
  - Deploy `scripts/fix_ai_assist_and_analyze_comment.py` to the live Helpdesk site when ready.
  - Smoke test `AI - Ticket Assist Menu` on a real HD Ticket with Vietnamese content.
  - Decide later whether AI drafts should stay as internal comments or fill/send the public reply composer.
- Current Phase: ticket CC shipped to GitHub/main; production deploy/migrate remains
- Working Context: AI Reply Copilot upgrade is documented in `openspec/changes/ai-reply-copilot-upgrade/`. The patch keeps existing Desk script endpoints stable, adds up to 3 ranked reply options, auto-selects the highest-confidence option, uses richer ticket/recent-message context, and enforces Vietnamese with accents. Local `./test_gate.sh` passed after adding regression tests.

- What Failed: Bulk-deleted inactive Desk scripts when the user asked to rewrite/refactor them.
- Why It Failed: Interpreted "xóa code rác" too broadly and treated inactive records as removable inventory instead of legacy code to rewrite.
- How to Prevent: For production Desk-managed scripts, export first, then update/refactor records in place. Do not delete records unless the user explicitly approves deletion after seeing the rewrite inventory.
- Scope: site:haravandesk.s.frappe.cloud scripts

## Mistakes & Learnings

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
