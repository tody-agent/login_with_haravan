# Design: Haravan Helpdesk Handoff Manual

## Context & Technical Approach

Haravan needs a Vietnamese handoff guide for staff who will operate and configure the production Frappe Helpdesk site. The guide should live in the existing VitePress docs and focus on practical operations rather than source-code internals only.

## Proposed Changes

### `docs/sop/haravan-helpdesk-handoff.md`
- Add a single operator-facing manual covering ticket template fields, field dependencies, product suggestion configuration, scripts, tokens, DocTypes, permissions, and FAQ.
- Explain which changes are pure Desk configuration and which require source-code edits in `login_with_haravan`.
- Avoid storing real secrets. Document Site Config key names only.

### `docs/.vitepress/config.mts`
- Add the handoff page under `SOP & Hướng dẫn` so it appears on the deployed VitePress site.

## Verification

- Run VitePress build from `docs/`.
- Confirm git diff only contains the planned docs/config/continuity files.
