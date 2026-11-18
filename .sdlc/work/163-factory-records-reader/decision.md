DECISION: READY

**Why.** All six reviewers passed in round 1 (code, security, test, behaviour, ui, ux), and the gate record is `GATE: PASS` on `./check.sh`. The test reviewer matched each requirement (R1–R11) to a named test in `tests/test_modules.py` or an existing pin that now reads the new module. The builder ran `status --all` with the base branch's script and with the changed one, and the outputs were identical. `plan.md` records where the build differs from the spec: the git-reading callables take paths relative to the change's folder, `MOVES_RE` is exempted by hand, the gate lists are keyed `round`/`land`, and one `LAND_STOPS` pin was dropped. Each has a stated reason, and none suggests the spec was wrong.

**Open items**
- None. The three nits (F1 and F2 from code, F3 from test) are in `findings.md` as `recorded`, not as CHANGEs.

**Decisions to confirm**
- None. There is no `decisions.md`, no open default and no blocking question.

**For the person at ship**
- Start with `scripts/closing.py`, which is a `[review] sensitive` path. Check that `_branch_files()` and the three adapters (`_factory_files`, `_agent_sessions`, `_agent_models`) still run the same git reads as before. `session_roles` now uses a recursive `ls-tree -r` listing, and a `len(parts) != 2` filter keeps it to direct children of `runs/`. Also check that `measure_change`'s `try`/`rework=failed` handling is unchanged.
- Run `git diff <base> -- tests/` to check R8: apart from the new tests, only reads of moved names should change. Two pins were removed on purpose: `test_metrics.py`'s `opening` pin, which was merged into `test_board.py`'s, and the `FACTORY_LAND_STOPS == board.LAND_STOPS` line. `LAND_STOPS` now has no pin against `factory.py`; only the board's `LAND_AT` test still checks it against `LAND_STEPS` (F2).
- In `history_samples`, the gate-list keys changed from `round-`/`land-` to `round`/`land`. Check that nothing outside the function reads those keys.
- 162 (lead time) also touches close's measure step. Whichever of the two lands second has to put its reader into `factory_records.py`, or R5's test fails.
- Optional: F1, the over-width lines in AGENTS.md around line 68.

- IMPACT: none — an internal move of core's copies of the factory's record parsing into one module. `status`, the board, the hand gate and close's trailers come out the same, and no command, config key or record format changes.

**Each undone item's disposition**
- None. `notes.md` doesn't exist, and the builder reports nothing left over.

**How to recover**
- The prompt names no irreversible paths. `plan.md`'s Rollback is a `git revert` of the change's commit: it writes no data and publishes nothing.
