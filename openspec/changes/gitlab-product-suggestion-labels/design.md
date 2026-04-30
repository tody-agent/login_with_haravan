# Design: GitLab Product Suggestion Labels

## Context & Technical Approach
GitLab issue creation is driven by the production `HD Form Script` named `GitLab - Ticket Issue Button` and the `Server Script` API method `haravan_helpdesk.api.gitlab_popup_v2`.

When an agent opens the GitLab popup on an `HD Ticket`, the popup already calls the API with `action=init`. This is the safest place to enrich the UI with default labels because the backend can read the ticket and the `HD Ticket Product Suggestion` record without exposing extra permissions or client-side database calls.

## Proposed Changes

### GitLab Popup API
- Read `HD Ticket.custom_product_suggestion`.
- Look up the matching `HD Ticket Product Suggestion.gitlab_labels`.
- Build default GitLab labels from the existing base labels plus product suggestion labels.
- Return `default_labels` in the `init` response.
- Use the same default labels on `create` if the client sends an empty labels value.

### GitLab Popup Form
- Use `init.default_labels` as the initial value for the Labels input.
- Keep the field editable so agents can add or remove labels before creating the GitLab issue.

### Deployment Script
- Add an idempotent patch script that fetches the live Frappe records, writes timestamped backups, applies narrow string transformations, validates the JavaScript parse, and updates production records through REST API.

## Verification
- Run the local test gate.
- Run the patch script with production API credentials.
- Open a ticket with `custom_product_suggestion` set and confirm the GitLab popup shows product labels before issue creation.
