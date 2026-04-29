# Design: Ticket Autofill Personalization

## Context & Technical Approach
Agents should only enter the operational fields they know: `Link Web / MyHaravan` and `Product Suggestion`. The system should resolve linked customer metadata and product taxonomy automatically, while hiding fields that are derived data.

The backend remains the source of truth. A Helpdesk SPA script improves the create-ticket UI and injects resolved values into the create payload when available, but the `HD Ticket` document hook also fills values during validation so fast submits or frontend changes do not lose data.

## Proposed Changes

### `login_with_haravan/setup/install.py`
- Ensure `HD Ticket` custom fields exist for link/domain/org/product metadata.
- Mark `Link Web / MyHaravan` and `Product Suggestion` required.
- Hide/read-only derived custom fields: `Org ID`, `MyHaravan Domain`, `Product Line`, `Product Feature`.

### `login_with_haravan/engines/ticket_autofill.py`
- Resolve `HD Customer`, `MyHaravan Domain`, and `Org ID` from a submitted web/MyHaravan value.
- Parse `Product Suggestion` into `Product Line` and `Product Feature`.
- Apply derived values to an `HD Ticket` document during validation.

### `login_with_haravan/ticket_context.py`
- Expose whitelisted APIs for the Helpdesk create-ticket page to fetch field metadata and resolve current values.

### `login_with_haravan/public/js/ticket_autofill.js`
- Activate only on Helpdesk new-ticket routes.
- Hide derived fields and the standard Customer field from agents.
- Watch `Link Web / MyHaravan` and `Product Suggestion`, resolve values server-side, and inject them into create-ticket payloads.

## Verification
- Add unit tests for product suggestion parsing and document autofill.
- Run `./test_gate.sh`.
