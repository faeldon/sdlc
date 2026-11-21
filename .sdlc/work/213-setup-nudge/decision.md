DECISION: READY

**Why:** All three round-1 reviewers returned PASS. The gate record (`./check.sh`, 3686 passed) is green, and R1–R11 each have code and a test. The change adds no write and no subprocess, and the nudge still never makes `vet --strict` refuse. The only open item is D1, which the spec's Contracts section already flags for the person to accept.

**Open items:**
- NIT, code reviewer: AGENTS.md:218 has a short line in the reflowed *Setup* paragraph that could be rewrapped. Minor.
- NIT, test reviewer: tests/test_setup_lifecycle.py:735 never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned. Minor.
- Neither NIT is in `notes.md`, which doesn't exist for this change.

**Decisions to confirm:**
- CONFIRM: D1: The build lets the startup hook run `drift`'s local file reads, plus one cached git call, while a repo's setup record is behind the plugin. That goes beyond the intent's "a file read". It adds no write, applies only until setup next records, and a current record is still one file read. The spec's Contracts section flags it and its Alternatives rejects re-recording, so the person's yes at the landing is enough.

**For the person at ship:**
- Look first at `setup_nudge()` and `drift_pending()` in `scripts/sdlc.py`, and at `hook_line()`. Check that the setup half sits in its own `try`, so a raising `drift` prints nothing and exits 0.
- Next, the skill edits in `skills/status/SKILL.md` and `skills/intent/SKILL.md`, which now pass `■ Setup` on.
- The hook contract changed, so look at `hooks/hooks.json`, REFERENCE.md *After an update*, and AGENTS.md *Updates*.
- No published interface that wasn't already approved is touched. The hook's new line is the spec's own, with its Contracts item approved with the spec.

- IMPACT: patch — anyone on the previous release merely gets a clearer setup nudge, which clears itself after a release that changes no defaults. Nobody has to do anything differently.

No unticked `- [ ]` items exist, since `notes.md` is absent, so there are no UNDONE lines.
