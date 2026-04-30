# Tasks: CC Email Smoke Test

## 1. Plan And Baseline

- [x] Create a focused smoke-test plan.
- [x] Capture live app version and production CC script state.
- [x] Capture baseline recent Email Queue and Error Log state.

## 2. Browser Execution

- [x] Open `https://haravan.help/helpdesk/tickets/new`.
- [x] Log in with the supplied agent account if redirected.
- [x] Create a ticket with `raised_by = sociads@gmail.com`.
- [x] Set `custom_cc_emails = hai.minh@outlook.com`.
- [x] Record ticket id, screenshots, and runtime notes.

## 3. Backend Verification

- [x] Verify the ticket stores the CC email.
- [x] Verify Email Queue or Communication references the CC recipient.
- [x] Verify no new related Error Log was created.

## 4. Debug/Fix

- [x] If verification fails, diagnose the exact source-controlled or production-script gap.
- [x] Apply the smallest safe fix.
- [x] Re-run the failed verification step.
