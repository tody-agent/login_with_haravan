# Agent Handoff

## What This Package Is

This folder is a standalone, deployable Frappe custom app. It should be treated as the source of truth for the Haravan login integration.

It is intentionally separated from:

```text
/Volumes/Data/Haravan/Haravan-CLI
```

## Current State

- App code is implemented.
- Local tests pass.
- Frappe Cloud packaging issues have been addressed.
- Known active issue is Haravan OAuth configuration: `invalid_request Invalid redirect_uri`.

## Where To Start

1. Read `openspec/project.md`.
2. Read `openspec/changes/haravan-social-login/design.md`.
3. Read `.cm/CONTINUITY.md`.
4. Read `docs/NEXT_STEPS_FOR_AGENT.md`.
5. Inspect `login_with_haravan/setup/install.py`.
6. Inspect `login_with_haravan/oauth.py`.

## Safe Next Coding Tasks

- Use `login_with_haravan.diagnostics.get_haravan_login_status` to inspect masked Social Login Key and Site Config status.
- Keep extending tests for setup/config parsing when adding new credential aliases.
- Add a management command/script to print the exact authorize URL Frappe will generate.
- Add better user-facing error pages for failed Haravan callbacks.

## Do Not Do

- Do not add Haravan commerce API scopes unless a new feature needs them.
- Do not move tests back to root `tests/`.
- Do not rename the Python package to `login-with-haravan`.
- Do not deploy a separate callback service unless Frappe-hosted callback is proven impossible.
