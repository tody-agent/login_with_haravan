# Design: AI Reply Copilot Upgrade

## Context & Technical Approach

The current AI assist feature is managed through production Desk scripts and patched from `scripts/fix_ai_assist_and_analyze_comment.py`. To keep endpoint compatibility, this change does not rename API methods or migrate logic into app whitelisted APIs yet.

The upgrade improves the existing contract:

- `generate-ai-reply` still performs one Gemini call.
- The prompt now includes ticket fields, 10 recent communications in chronological order, and recent internal notes.
- Gemini is instructed to return up to 3 scenario-based reply options in accented Vietnamese.
- The server script normalizes the response and returns `selected_index` based on highest confidence.
- The HD Form Script dialog renders radio choices and fills the editable textarea with the selected option.

## Proposed Changes

### `scripts/fix_ai_assist_and_analyze_comment.py`

- Update AI assist UI copy to Vietnamese with accents.
- Add radio option rendering for reply suggestions.
- Auto-select the API-provided `selected_index`; fallback to highest confidence.
- Keep `send-ai-reply` as internal comment insertion for safety.
- Expand `generate-ai-reply` prompt data with richer ticket context.
- Normalize option schema to `label`, `scenario`, `confidence`, `reason`, `missing_context`, and `content`.

### `login_with_haravan/tests/test_helpdesk_ai_scripts.py`

- Add regression tests for the three-option contract.
- Add regression tests for ticket/recent-message context.
- Add regression tests for radio UI and accented Vietnamese strings.

## Verification

- `python3 -m py_compile scripts/fix_ai_assist_and_analyze_comment.py`
- Extract `ASSIST_MENU_SCRIPT` and run `node --check`.
- `python3 -m unittest login_with_haravan.tests.test_helpdesk_ai_scripts -v`
- `./test_gate.sh`

## Out of Scope

- Directly emailing customers from the AI dialog.
- Migrating AI Server Scripts into source-controlled Python whitelisted APIs.
- Changing Gemini/OpenRouter provider selection.
