# Implementation Checklist

- [x] 1.1 Review current AI assist patch script and Desk script registry.
- [x] 1.2 Qualify the product problem with cm-brainstorm-idea.
- [x] 1.3 Document recommended approach in `proposal.md`.
- [x] 2.1 Update reply dialog to show radio options and auto-select the strongest scenario.
- [x] 2.2 Update reply prompt to require accented Vietnamese and up to 3 ranked options.
- [x] 2.3 Include ticket fields, latest communications, and internal notes in the AI context payload.
- [x] 2.4 Normalize model output before returning it to the UI.
- [x] 3.1 Add regression tests for AI reply prompt/UI contract.
- [x] 3.2 Compile the patch script.
- [x] 3.3 Check embedded JavaScript syntax.
- [x] 3.4 Run full local test gate.

## Later Follow-up

- [ ] Move AI Server Script logic into source-controlled Frappe whitelisted APIs.
- [ ] Decide whether the dialog should insert a private comment, fill the public reply composer, or send customer email directly.
