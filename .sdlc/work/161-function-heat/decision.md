DECISION: READY

**Why.** Both reviewers in round 1 (code and behaviour) returned `VERDICT: PASS`. Neither raised a Critical or High finding. The gate is green: `./check.sh` exited 0, with 2944 passed and 28 skipped. Each Outcome and Constraint in the intent can be traced to a test or a check: seven `portable` tests, two acceptance checks, and a Windows entry in `tests/test_windows.py`. Nothing under `scripts/` changed. All three defaults are answered word for word by the intent's own Outcome or Approach.

**Open items**
- None. The only finding is F1, a nit raised by `code` and recorded in `findings.md`: add a one-line comment at `.sdlc/function-heat.py:123` about the `--root` blame edge. It isn't a requested change.

**Decisions to confirm**
- SETTLED: D1: The intent's Outcome says the output is "a plain-text table", which answers its own open question about the format. The output is read only by this repo's `retro.indicators`, so it is no published interface. Both reviewers found it consistent with the intent (code.md Notes, behaviour.md Notes).
- SETTLED: D2: The intent's Outcome says "ranked by commits then size", the same order as the hand-run analysis it cites. The code reviewer confirmed the ranking against Outcome 1, and a test pins "commits, then size, cut to the top N" (build/round-1.md).
- SETTLED: D3: The intent's Approach specifies `git blame --line-porcelain` and counts the distinct commits after the boundary within each function's range. The builder implemented exactly that, and the code reviewer marked the porcelain parsing as done well. Choosing a more exact diff walk instead would be a new approach, not a gap in this one.

**For the person at ship**
- Read `.sdlc/function-heat.py` first. Check that the boundary search matches `sdlc.py retro`'s: the newest `Retrospective YYYY-MM-DD` commit on the base branch's first-parent line. Also check how the base branch is resolved (`[git] base`, then `main`, then `origin/HEAD`). AGENTS.md doesn't allow hard-coding `main`, and this script falls back to `main` by name, the same way `_resolve_trunk()` detects it.
- Neither reviewer ran `sdlc.py retro` end to end. The builder called `retro._evidence` directly with the real config, and it exited 0 in 0.6s. A full `sdlc.py retro` from the main checkout after landing would confirm that `architecture.host` shows the table.
- `tests/test_windows.py` is outside the intent's Affected list. The builder added it because it is the test behind the Windows constraint, and that reason holds.
- The `[review]` edit in `.sdlc/config.toml` (nit 2026-11-18-102) should change only the comment. Confirm that none of the `sensitive` or `irreversible` values moved.

- IMPACT: none — this is the plugin repo's own retrospective indicator, under `.sdlc/`, plus tests. Nothing a host installs or runs changes.

**Undone items**
- None. This change has no `notes.md`, and the builder reports nothing left over.
