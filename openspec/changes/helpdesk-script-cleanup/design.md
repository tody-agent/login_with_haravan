# Design: Helpdesk Script Cleanup

## Context

Production has Desk-managed scripts for:

- `HD Form Script`: confirmed from backup `backups/haravandesk_hd_ticket_form_20260430_075916/backup.json`.
- `Server Script`: needs authenticated export from `https://haravan.help/desk/server-script`.
- `Client Script`: needs authenticated export from `https://haravan.help/desk/client-script`.

Unauthenticated REST and Desk page access are blocked by Frappe permissions, so cleanup must start with an authenticated export before any delete operation.

The confirmed `HD Ticket` backup contains 12 form scripts, 9 enabled and 3 disabled. The heaviest scripts are:

| Script | Status | Approx lines | Role |
| --- | --- | ---: | --- |
| `HD Ticket Intake Dependencies` | enabled | 798 | Ticket intake field filters, phone/customer lookup, DOM patches |
| `HD Ticket - GitLab Popup V3` | enabled | 412 | GitLab search/create/link popup |
| `AI Reply Summary Actions` | enabled | 355 | AI summary/reply/send actions |
| `Custom Button - Customer Profile` | enabled | 198 | Bitrix customer profile panel |
| `HD Ticket - AI Analyze Actions` | enabled | 89 | AI classification/analyze action |
| 4 `Field Dependency-*` scripts | enabled | 28 each | Auto-generated service field filters |
| `HD Ticket - Raised By Lookup Suggestions` | disabled | 232 | Older email/customer lookup |
| `HD Ticket Agent Intake Autofill UX` | disabled | 134 | Older agent intake DOM patch |
| `HD Ticket - Runtime Probe` | disabled | 44 | Debug probe |

## Current Problems

### 1. Too much behavior lives in browser form scripts

`HD Ticket Intake Dependencies` handles several responsibilities at once: product options, function options, required-field UI, hidden derived fields, phone normalization, contact lookup, customer history lookup, and direct DOM patching. This makes regressions likely because one script controls unrelated workflows.

### 2. Debug and probe code is still present

`AI Reply Summary Actions` and `HD Ticket - Runtime Probe` call `haravan_helpdesk.api.gitlab_popup_v2` only for debug ping / DOM probe purposes. This should not remain in production form logic.

### 3. Duplicate customer profile implementations exist

The custom app already includes `login_with_haravan/public/js/customer_profile_panel.js`, but production also has `Custom Button - Customer Profile` as an `HD Form Script`. Both render a Bitrix/customer profile panel and call server-side profile APIs, so ownership is split.

### 4. Field dependency logic is split and inconsistent

There are four auto-generated `Field Dependency-*` scripts plus custom dependency code inside `HD Ticket Intake Dependencies`. Some service dependencies check `User guide`, while DocField `depends_on` values mostly point to `Onboarding Service`, so workflow rules are hard to reason about.

### 5. Disabled scripts are still operational risk

Three disabled scripts appear to be old experiments or probes. They are not active but can be accidentally re-enabled, and they obscure which flow is canonical.

### 6. Server Script and Client Script inventory is missing from source control

The repo documents that AI/GitLab/Bitrix server logic may live in Server Scripts, but those scripts are not exported in this repository. This blocks safe deletion because client-side call targets must be matched to live server-side implementations first.

## Target Architecture

Use a smaller ownership model:

| Layer | Owner | Responsibility |
| --- | --- | --- |
| Custom app Python | `login_with_haravan/engines/`, API modules | Token handling, Bitrix/GitLab/AI calls, permission checks, data enrichment |
| Desk Server Scripts | Temporary compatibility only | Small wrappers around source-controlled Python methods, if needed |
| HD Form Script | Thin UI adapters only | Add action buttons, call one stable API, render minimal result |
| Field Dependencies / Template | Desk configuration | Simple parent-child select/link filtering |
| Custom app public JS | `login_with_haravan/public/js/` | Global Helpdesk portal behavior: login redirect, org selector, profile panel |

## Proposed Cleanup Strategy

### Phase 0. Export and Freeze

Export all `HD Form Script`, `Server Script`, and `Client Script` records with full fields into a dated backup directory. Do not delete anything until every client call target is mapped to a server implementation.

### Phase 1. Classify Scripts

Classify each script as:

- `keep`: still needed as-is.
- `merge`: needed but should be merged into a single canonical script.
- `move-to-app`: business logic/API should move into source-controlled Python or public JS.
- `disable-first`: likely trash, disable and observe before delete.
- `delete`: confirmed unused/debug/duplicate with backup.

Initial classification from the available HD Form Script backup:

| Script | Classification | Reason |
| --- | --- | --- |
| `HD Ticket - Runtime Probe` | delete | Debug-only probe, disabled |
| `HD Ticket Agent Intake Autofill UX` | delete after confirm | Disabled predecessor of `HD Ticket Intake Dependencies` |
| `HD Ticket - Raised By Lookup Suggestions` | delete after confirm | Disabled predecessor; overlaps with intake script lookup |
| `Custom Button - Customer Profile` | merge/delete after confirm | Duplicate of app-owned profile panel |
| `AI Reply Summary Actions` | refactor | Keep user feature, remove debug ping and duplicate send handling |
| `HD Ticket - AI Analyze Actions` | merge/refactor | Keep feature if still used, align with AI summary/reply backend |
| `HD Ticket - GitLab Popup V3` | refactor | Keep feature if GitLab is active, remove version/debug naming and isolate API wrapper |
| `HD Ticket Intake Dependencies` | split/refactor | Too broad; reduce to field filters and UI glue only |
| 4 `Field Dependency-*` scripts | replace with Desk field dependency if possible | Auto-generated and simple enough to configure declaratively |

### Phase 2. Build a Call Graph

Map every browser-side call target:

- `generate-ai-summary`
- `generate-ai-reply`
- `send-ai-reply`
- `haravan_ai_analyze_ticket`
- `haravan_helpdesk.api.gitlab_popup_v2`
- `haravan_bitrix_customer_profile`
- `haravan_raised_by_ticket_context`
- `frappe.client.get`
- `frappe.client.get_list`
- `login_with_haravan.customer_profile.get_ticket_customer_profile`
- `login_with_haravan.oauth.get_user_haravan_orgs`

For each endpoint, record:

- Source owner: custom app Python, Server Script, or core Frappe.
- Permission model.
- Secret source: Site Config only, never browser.
- Active callers.
- Replacement path if it is moved.

### Phase 3. Refactor by Workflow

Refactor by user workflow instead of by historical script name:

1. Customer ticket intake.
2. Agent ticket classification.
3. AI actions.
4. GitLab issue linkage.
5. Customer profile lookup.

Each workflow should have one UI adapter and one server API boundary.

### Phase 4. Delete Safely

Use a two-step production cleanup:

1. Disable suspected trash for an observation window.
2. Delete only after smoke tests and audit logs show no active calls.

For already disabled scripts, deletion can happen sooner, but only after the export backup is verified.

## Verification

Minimum verification before and after each phase:

- Export backup exists and can be restored.
- `HD Ticket Template > Default` still contains required fields.
- Customer can create ticket from `/helpdesk/my-tickets/new`.
- Multi-org customer selector still sets `customer`.
- Agent can open existing ticket.
- AI summary/reply/analyze paths either work or are intentionally disabled.
- GitLab popup either works or is intentionally disabled.
- Customer Profile panel opens and returns Bitrix status without exposing tokens.
- `PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v`
- `python3 -m compileall -q login_with_haravan`
