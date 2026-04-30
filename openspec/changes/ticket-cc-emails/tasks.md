# Tasks: Ticket CC Emails

## 1. Metadata

- [x] Add `custom_cc_emails` setup for `HD Ticket`.
- [x] Add an idempotent `HD Ticket Template > Default` row for agent-only launch.

## 2. Email Logic

- [x] Add pure CC parsing, validation, normalization, and merge logic.
- [x] Validate/normalize `HD Ticket.custom_cc_emails` on save.
- [x] Merge ticket CC into agent replies before Helpdesk calls `frappe.sendmail`.
- [x] Include ticket CC in agent-created acknowledgement emails when acknowledgement is sent.

## 3. Verification

- [x] Add tests for parser/merge/setup/reply/acknowledgement behavior.
- [x] Run targeted tests.
- [x] Run full `npm run test` quality gate.
