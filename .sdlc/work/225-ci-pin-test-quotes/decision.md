DECISION: READY

**Why:** The change touches only `tests/test_ci.py`, as the intent says. A quoted SHA pin with its `# v…` comment now passes. A quoted tag, a quoted branch and a mismatched quote pair are still refused. `unpinned()`'s docstring now gives the Dependabot reason for `VERSION`. Both reviewers returned PASS with nothing open, and the round-1 gate record reads `GATE: PASS`.

**Open items:**
- None. The code reviewer's one NIT (`QUOTED` is a module-level regex) matches the file's existing style and needs no change.

**Decisions to confirm:**
- SETTLED: D1: The intent's Approach leaves flow-mapping `uses:` out. Its Affected section says nothing outside `tests/test_ci.py` reads the check. The intent also notes that no workflow here writes that form, and the behaviour reviewer found the default consistent with the Approach.

**For the person at ship:**
- Look at the `QUOTED` regex and the quote-stripping in `unpinned()` in `tests/test_ci.py`, and at the five new cases in `test_the_check_refuses_a_tag_or_branch_pin`.
- No published interface is touched (the intent's *Contracts* is "none").
- Shipping retires nits 2026-11-22-6 to -10, which the intent lists.

- IMPACT: none — only a repo-internal test changed; nothing anyone receives is different.

**Undone items:** none, since there is no `notes.md`.
