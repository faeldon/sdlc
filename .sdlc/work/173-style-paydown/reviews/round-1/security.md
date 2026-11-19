VERDICT: PASS

## Notes

I found no security issues. Every edit in this change is to comments or prose, and none of it can run.

**Trust boundaries the change touches:** none in practice.
- **`check.yml`**, which is `[review] sensitive`: only the header comment changed (lines 1–6, rewrapped). The `on:` triggers, permissions, jobs and steps are byte-for-byte the same, so nothing changes about who can trigger CI or what it may do.
- **`check.sh`**: one comment grew by two lines to answer -76. The `ruff`, `pytest -q -n auto` and `validate` commands are unchanged, so the gate is no weaker.
- **`.sdlc/function-heat.py`**: a two-line comment above the `blame` call. The code's logic is unchanged.
- **`AGENTS.md` and `plugins/factory/README.md`**: rewraps only. A diff of the word sequences before and after found them identical.
- **`plugins/factory/agents/reviewer-code.md` and `reviewer-ux.md`**: each paragraph is only rewrapped. No instruction, permission, tool or verdict rule changed, so the agents' prompts cover what they did before. The frontmatter `description:` lines, which the harness reads, are untouched (decision D1, the builder's default, which I agree with: a multi-line YAML value is a change the harness has to parse, not a rewrap).

**What I checked:**
- No secret, token or personal path appears in the diff or in the change's own files.
- No dependency was added.
- Nothing that deletes, overwrites, pushes or publishes is affected.
- The gate record `build/round-1.gate.md` says PASS, exit 0, tree unchanged.

**What I ran:** `git status`, `git diff` on the CI, `check.sh`, heat-script and agent files, and the word-sequence comparison on `AGENTS.md` and the factory README. Nothing else.

**Done well:** each edit is kept apart. The only places with new words are the two comments the intent allows (-76 and -108); everything else is a rewrap.
