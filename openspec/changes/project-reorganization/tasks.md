# Implementation Checklist
- [ ] 1.1 Move internal files (`NEXT_STEPS_FOR_AGENT.md`, `AGENT_HANDOFF.md`, `SITE_CONFIG_HANDOFF.md`) to `openspec/`
- [ ] 1.2 Move internal folders (`jtbd/`, `personas/`, `sop/`) to `openspec/`
- [ ] 2.1 Update `.gitignore` to include `.wrangler/`
- [ ] 2.2 Update `AGENTS.md` paths to reflect the new location of `AGENT_NEXT_STEPS.md`
- [ ] 2.3 Update `docs/.vitepress/config.mts` to remove broken/internal links
- [ ] Verification testing (Run `npm run build` or `npx vitepress build docs` to verify VitePress integrity)
