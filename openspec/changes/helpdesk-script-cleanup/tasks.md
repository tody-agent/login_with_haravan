# Implementation Checklist

- [x] 1.1 Export authenticated `HD Form Script`, `Server Script`, and `Client Script` records to `backups/haravandesk_scripts_<timestamp>/`.
- [x] 1.2 Generate an inventory table: name, enabled/disabled, DocType, script type, line count, API calls, fields touched.
- [ ] 1.3 Build a call graph from browser scripts to Server Scripts/custom app Python methods.
- [ ] 1.4 Mark each script as `keep`, `merge`, `move-to-app`, `disable-first`, or `delete`.

- [x] 2.1 Delete or archive confirmed debug-only scripts: start with `HD Ticket - Runtime Probe`.
- [x] 2.2 Confirm disabled predecessors are unused, then remove `HD Ticket Agent Intake Autofill UX` and `HD Ticket - Raised By Lookup Suggestions`.
- [x] 2.3 Remove debug pings from `AI Reply Summary Actions`.

- [x] 3.1 Decide canonical owner for Customer Profile: prefer `login_with_haravan/public/js/customer_profile_panel.js` plus `login_with_haravan.customer_profile.get_ticket_customer_profile`.
- [ ] 3.2 Disable/delete duplicate `Custom Button - Customer Profile` after confirming the app-owned panel covers the same workflow.
- [ ] 3.3 Verify Bitrix profile panel smoke test on an existing ticket.

- [x] 4.1 Split `HD Ticket Intake Dependencies` into a small declarative field dependency layer and a thin UI adapter.
- [ ] 4.2 Move customer/contact lookup and suggestion business rules to server-side code or a single source-controlled API.
- [ ] 4.3 Replace the four simple `Field Dependency-*` scripts with Desk Field Dependency configuration where possible.
- [ ] 4.4 Remove duplicate fields or normalize naming for `custom_my_haravan_domain` vs `custom_myharavan_domain`.

- [x] 5.1 Consolidate AI scripts into one `HD Ticket AI Actions` adapter with shared API response handling.
- [x] 5.2 Consolidate GitLab script naming/API contract; remove V3/V5/debug naming from production UI.
- [ ] 5.3 Ensure AI/GitLab tokens are read only server-side from Site Config.

- [ ] 6.1 Run source tests: `PYTHONPATH=. python3 -m unittest discover -s login_with_haravan/tests -v`.
- [ ] 6.2 Run compile check: `python3 -m compileall -q login_with_haravan`.
- [ ] 6.3 Run Helpdesk smoke tests for ticket creation, ticket open, AI actions, GitLab popup, Customer Profile panel.
- [x] 6.4 Keep rollback notes with the dated export backup and exact scripts deleted/disabled.
