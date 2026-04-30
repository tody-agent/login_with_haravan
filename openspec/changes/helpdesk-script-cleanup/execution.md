# Execution: Helpdesk Script Cleanup

## 2026-04-30 Cleanup

Target site:

```text
https://haravandesk.s.frappe.cloud
```

Public domain:

```text
https://haravan.help
```

## Backup

Authenticated REST export was saved before deletion:

```text
backups/haravandesk_scripts_20260430_123257/
```

Exported records:

| DocType | Count |
| --- | ---: |
| `HD Form Script` | 9 |
| `Client Script` | 4 |
| `Server Script` | 31 |

All exported records were inactive at the time of cleanup:

- `HD Form Script.enabled = 0`
- `Client Script.enabled = 0`
- `Server Script.disabled = 1`

## Deleted Then Restored

Inactive Desk-managed script records were deleted, but this was the wrong action for the requested scope. The intent was to rewrite/refactor, not remove. A rollback was immediately performed from the backup.

Initially deleted:

| DocType | Deleted |
| --- | ---: |
| `HD Form Script` | 9 |
| `Client Script` | 4 |
| `Server Script` | 31 |

Delete report:

```text
backups/haravandesk_scripts_20260430_123257/delete_report.json
```

Errors: `0`

## Restore

Restored from backup:

| DocType | Restored |
| --- | ---: |
| `HD Form Script` | 9 |
| `Client Script` | 4 |
| `Server Script` | 31 |

Restore reports:

```text
backups/haravandesk_scripts_20260430_123257/restore_report.json
backups/haravandesk_scripts_20260430_123257/restore_scheduler_report.json
```

Three scheduler-event `Server Script` records required deleting orphaned stopped `Scheduled Job Type` rows before restore:

- `Haravan WOC Reminder 4h`
- `Haravan WOC Auto Close 24h`
- `Haravan Renewal Alert T90`

The three orphaned scheduled jobs were `stopped = 1` and no `Server Script` scheduler records existed at that moment.

## Verification

Post-restore REST verification:

| DocType | Count | Active-like Count |
| --- | ---: | ---: |
| `HD Form Script` | 9 | 0 |
| `Client Script` | 4 | 0 |
| `Server Script` | 31 | 0 |

The site is back to the pre-cleanup script count and inactive state. `frappe.clear_cache` via REST returned `403 FORBIDDEN`, so cache clear should be done from Desk/Frappe Cloud UI if stale script behavior appears.

## Rewrite

After restore, the 9 `HD Form Script` records were rewritten in place and kept disabled:

```text
backups/haravandesk_scripts_20260430_123257/rewrite_hd_form_script_report.json
```

Line count after rewrite:

| Script | Lines | Enabled |
| --- | ---: | ---: |
| `AI Reply Summary Actions` | 111 | 0 |
| `Custom Button - Customer Profile` | 76 | 0 |
| `HD Ticket - AI Analyze Actions` | 29 | 0 |
| `HD Ticket - GitLab Popup V3` | 61 | 0 |
| `HD Ticket Intake Dependencies` | 46 | 0 |
| `Field Dependency-custom_internal_type-custom_service_line` | 17 | 0 |
| `Field Dependency-custom_internal_type-custom_service_name` | 17 | 0 |
| `Field Dependency-custom_internal_type-custom_service_onboarding_phrase` | 17 | 0 |
| `Field Dependency-custom_internal_type-custom_service_vendor` | 17 | 0 |

Verification:

- All rewritten `HD Form Script` records fetched back from production.
- No debug/probe markers found in rewritten `HD Form Script` content.
- `new Function(script)` parse check passed for all 9 rewritten scripts.
- All rewritten scripts remain `enabled = 0`, so live Helpdesk behavior is unchanged until an explicit enable/smoke-test step.

## User Decision Cleanup

After grouping the script responsibilities by business capability, the following user decisions were applied:

| Group | Decision |
| --- | --- |
| Haravan login/account creation | Keep |
| Customer enrichment | Keep; Haravan proactive enrichment is required, Bitrix remains backup/passive |
| Agent Customer Profile | Keep custom button/profile view |
| AI | Keep; consolidate into one AI menu/action group |
| GitLab | Keep |
| Ticket form field behavior | Keep basic dependency/required/validation; remove complex DOM/history lookup |
| Ticket data mapping | Keep important mapping; move toward server-side/source-controlled logic |
| Old workflow/WOC/Renewal | Remove for now |
| Attachments/inline media | Keep |
| KPI/dashboard APIs | Remove |
| Mock/probe/diagnostic/maintenance APIs | Remove |
| Email automation | Keep |

Backup before applying these decisions:

```text
backups/haravandesk_scripts_post_decision_20260430_130540/
```

Deleted by decision:

| DocType | Count |
| --- | ---: |
| `Client Script` | 3 |
| `Server Script` | 14 |

Delete report:

```text
backups/haravandesk_scripts_post_decision_20260430_130540/decision_delete_report.json
```

Remaining after cleanup:

| DocType | Count | State |
| --- | ---: | --- |
| `HD Form Script` | 9 | all disabled |
| `Client Script` | 1 | disabled |
| `Server Script` | 17 | all disabled |

Removed:

- Old workflow/WOC/Renewal scripts.
- KPI APIs.
- Mock/probe/diagnostic/maintenance APIs.
- Old duplicate Client Script UX for workflow/intake/autofill.

Kept:

- Haravan/account/enrichment-related scripts.
- AI APIs and form scripts.
- GitLab API and form script.
- Customer Profile / Bitrix API and form script.
- Basic field dependency/mapping/validation scripts.
- Attachment/inline media scripts.
- Email automation scripts.

Local verification after cleanup:

```text
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
python3 -m compileall -q login_with_haravan
```

Result: 71 tests passed; compile check passed.

Open point:

- Source code still has explicit tests and docs for the previous "login-only/no Haravan commerce enrichment" decision. The new requirement says proactive Haravan enrichment during login/register is needed.

## MCP Update: Haravan Login Enrichment

MCP connection verified:

```text
site: haravan
url: https://haravandesk.s.frappe.cloud/
authenticatedAs: maryfranceslatecia8151@gmail.com
```

Created/updated via MCP:

| DocType | Name | Type | Event | State |
| --- | --- | --- | --- | --- |
| `Server Script` | `Haravan Login Customer Enrichment` | `DocType Event` | `Haravan Account Link / After Save` | enabled |

Purpose:

- Runs after `Haravan Account Link` is inserted/updated during Haravan login/register.
- Enriches the linked `HD Customer` proactively.
- Reads config from Site Config first:
  - `haravan_customer_enrichment_enabled`
  - `haravan_customer_enrichment_url` or `haravan_customer_profile_api_url`
  - `haravan_customer_enrichment_token`
  - `haravan_customer_enrichment_auth_header`
- If no enrichment URL is configured, it still keeps identity fields safe and does not block login.
- If the API returns profile data, it maps known profile fields onto existing `HD Customer` custom fields when those fields exist.
- If `HD Customer Data` exists, it writes a `source = haravan` snapshot for successful enrichment.

Smoke test:

- Created temporary `HD Customer`: `999000123 - CODEX SMOKE TEST`.
- Created temporary `Haravan Account Link`, which triggered the Server Script.
- Verified `HD Customer` identity fields remained correct:
  - `domain = 999000123.myharavan.com`
  - `custom_haravan_orgid = 999000123`
  - `custom_myharavan = 999000123.myharavan.com`
- Deleted both temporary smoke-test documents.
- Verified both smoke-test documents are gone.

Current script counts after MCP update:

| DocType | Count | Active |
| --- | ---: | ---: |
| `HD Form Script` | 9 | 0 |
| `Client Script` | 1 | 0 |
| `Server Script` | 18 | 1 |

Local verification after MCP update:

```text
PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v
python3 -m compileall -q login_with_haravan
```

Result: 71 tests passed; compile check passed.

## Rename: Script Registry Cleanup

The Desk-managed script records were renamed on production to follow a short module-based convention:

```text
<Module> - <Flow/Context> <Action>
```

Modules now used:

- `Auth`
- `Profile`
- `AI`
- `GitLab`
- `Ticket`
- `Media`
- `Email`
- `Onboarding`

Documentation added:

```text
docs/guide/helpdesk-script-registry.md
```

Important implementation notes:

- `HD Form Script` supports `frappe.client.rename_doc`; 9 records were renamed in place.
- `Client Script` and `Server Script` do not allow direct rename on this site, so records were cloned to the new names with the same script body/state and the old records were deleted.
- Server Script API records kept their original `api_method` values, so existing client calls do not need route changes.
- A temporary migration API was used only to clone/delete Server Script records server-side, then deleted immediately.

Post-rename production inventory:

| DocType | Count | Active |
| --- | ---: | ---: |
| `HD Form Script` | 9 | 0 |
| `Client Script` | 1 | 0 |
| `Server Script` | 18 | 1 |

Enabled script after rename:

| DocType | Name | Type | Event | State |
| --- | --- | --- | --- | --- |
| `Server Script` | `Auth - Login Customer Enrich` | `DocType Event` | `Haravan Account Link / After Save` | enabled |

Verification:

- Old script names count is `0` across `HD Form Script`, `Client Script`, and `Server Script`.
- Temporary migration script count is `0`.
- Smoke test created a temporary `HD Customer` and `Haravan Account Link`, which triggered `Auth - Login Customer Enrich` without blocking save.
- Temporary smoke-test documents were deleted after verification.

## Activation And Smoke Test

All retained scripts were activated on production.

Post-activation inventory:

| DocType | Count | Active |
| --- | ---: | ---: |
| `HD Form Script` | 9 | 9 |
| `Client Script` | 1 | 1 |
| `Server Script` | 19 | 19 |

Additional script created during activation:

| DocType | Name | Type | API Method | State |
| --- | --- | --- | --- | --- |
| `Server Script` | `Onboarding - Agent Ticket API` | API | `haravan_agent_create_customer_ticket` | enabled |

Fixes applied during smoke test:

- Updated `GitLab - Ticket Issue Button` to call `detail` instead of a non-existent `current` action.
- Hardened `Onboarding - Create Ticket API` so missing input returns JSON instead of trying to create an invalid ticket.
- Added `Onboarding - Agent Ticket API` because the active Client Script button called `haravan_agent_create_customer_ticket`.
- Updated `Onboarding - Agent Ticket Dialog` to include required `custom_product_suggestion`.
- Ran a server-script cache nudge so the new API method became available, then deleted the temporary cache helper.

Smoke-test results:

| Group | Result |
| --- | --- |
| HD Form Script list | 9 active scripts returned by `hd_list_form_scripts` |
| AI summary API | Passed on smoke ticket |
| AI reply suggestion API | Passed on smoke ticket |
| AI analyze API | Passed with `dry_run=1` on smoke ticket |
| GitLab detail API | Passed on smoke ticket and existing linked ticket |
| Bitrix Customer Profile API | Passed; returned `Bitrix disabled` cleanly when config disabled |
| Onboarding API | Passed missing-input validation and create/delete smoke ticket |
| Agent Ticket API | Passed missing-input validation and create/delete smoke ticket |
| Login enrichment event | Passed create/delete `HD Customer` + `Haravan Account Link` smoke test |

Smoke-test cleanup:

- Temporary HD Tickets created for activation smoke tests were deleted.
- Temporary HD Customer and Haravan Account Link records were deleted.
- Temporary File record was deleted.
- Temporary migration/cache helper Server Scripts were deleted.

Known side effect:

- The first `haravan_ai_analyze_ticket` API test was run against existing ticket `44454` without `dry_run=1`; that API mutates ticket fields by default and reported updates to `agent_group` and `custom_product_feature`.
- Subsequent AI analyze tests were run with `dry_run=1` on a temporary smoke ticket to avoid further mutation.

## Restore Full GitLab Popup

After activation, the simplified GitLab popup was replaced with the full previously working popup from backup:

```text
backups/haravandesk_hd_ticket_form_20260430_075916/backup.json
```

Updated production script:

| DocType | Name | State | Notes |
| --- | --- | --- | --- |
| `HD Form Script` | `GitLab - Ticket Issue Button` | enabled | Restored full `GitLab Popup V5` UI |

Restored UI capabilities:

- Create a new GitLab issue and link it to the ticket.
- Search open GitLab issues, including IID lookup.
- Link an existing GitLab issue to the ticket.
- View current ticket-to-issue mapping.
- Sync linked issue details/comments.
- Unlink/remove ticket-to-issue mapping.

Verification:

- JavaScript parse check passed locally with `new Function(script)`.
- Production script fetched back with the full restored body.
- API `init` passed on ticket `44454`.
- API `search` passed and returned open GitLab issues.
- API `detail` passed on linked ticket `44454`.
- API `link` and `unlink` passed on a temporary smoke ticket.
- Temporary smoke ticket was deleted after verification.
- `create` action was restored but not executed during smoke test to avoid creating a junk GitLab issue.

## Rollback

Restore from the JSON backup files in:

```text
backups/haravandesk_scripts_20260430_123257/
```

The backup contains each original document body, including script content and enabled/disabled state at export time. Future work should continue rewriting/updating records in place rather than deleting them.
