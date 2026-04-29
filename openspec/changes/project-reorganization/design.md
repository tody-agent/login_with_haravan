# Design: Project Structure Reorganization

## Context & Technical Approach
The repository is currently mixing Frappe-native source code, public documentation (VitePress), internal planning/agent documents, and sensitive/build artifacts at the root and `docs/` level.
This creates a risk of exposing internal documents in the public documentation site and violates clean repository guidelines.
The approach is to strictly separate public-facing documentation (`docs/`) from internal agent/developer handoffs and plans (`openspec/`), while keeping the core Frappe App intact at the root.

## Proposed Changes

### `docs/` Directory
- **What changes:** Move all internal files out of `docs/`.
  - `docs/NEXT_STEPS_FOR_AGENT.md` -> `openspec/AGENT_NEXT_STEPS.md`
  - `docs/AGENT_HANDOFF.md` -> `openspec/AGENT_HANDOFF.md`
  - `docs/SITE_CONFIG_HANDOFF.md` -> `openspec/SITE_CONFIG.md`
  - `docs/jtbd/` -> `openspec/jtbd/`
  - `docs/personas/` -> `openspec/personas/`
  - `docs/sop/` -> `openspec/sop/`
- **Why this approach:** `docs/` is exclusively for VitePress public documentation.

### `docs/.vitepress/config.mts`
- **What changes:** Remove sidebar links to `AGENT_HANDOFF`, `SITE_CONFIG_HANDOFF`, `NEXT_STEPS_FOR_AGENT`, and any other moved files.
- **Why this approach:** To prevent 404s and remove internal topics from the public table of contents.

### `.gitignore`
- **What changes:** Add `.wrangler/` to the ignore list.
- **Why this approach:** `.wrangler/` is a build artifact from Cloudflare Pages and must not be committed.

### `AGENTS.md`
- **What changes:** Update the reference to `NEXT_STEPS_FOR_AGENT.md` to point to its new path `openspec/AGENT_NEXT_STEPS.md`.
- **Why this approach:** So the CodyMaster agents can continue to find their instructions.

## Verification
- Run VitePress build locally to ensure no 404 broken links.
- Check `git status` to ensure `.wrangler/` is ignored.
- Read `AGENTS.md` to ensure it points to the correct new path.
