DECISION: READY

**Why**

All 13 requirements are built, and each has a test or an acceptance check. All four reviewers (code, security, test, behaviour) passed round 1. The gate is green: `./check.sh` exit 0, 3254 passed. The few departures from the plan are small, and `plan.md` was updated to explain them: the eject output now always has a `problems` key, `train --run` passes an eject's problem along on its undo, and `TRIAGE_SUBJECT` replaces a literal in `_inbox_commit()`. Nothing in the rounds suggests the spec was wrong. The behaviour check's `retro` run found the restored-entry case the intent describes (entry 2026-11-18-68 filed again after 166's `Close` retired it).

**Open items**

None. The five findings are all nits:
- F1 (code): no failing-append test for `_train_stop`. Recorded.
- F2 and F3 (code): an unguarded `_log_blocks` call when `trunk` is empty, and `_closing_subject` defined after its first use. Both minor.
- F4 and F5 (test): no assertion on the `unknown` rows' `change` key, and none that a stop before any commit leaves no row. Recorded.

**Decisions to confirm**

None. D-R1 (reuse 174's `runs/ejections.jsonl`) is ticked and decided by the person, and the build follows it. No ejection file of its own was added; it reads under `EJECTIONS`. No defaults are open.

**For the person at ship**

- **Look first at `plugins/factory/scripts/landing.py`** (sensitive): `_record_ejection(folder, cause, train)`. Check that the new `train` key goes last, and that an `OSError` comes back as a problem and never blocks. Then check how `_train_eject()`, `_train_stop()` and the `train --run` undos pass that problem on.
- **Then `scripts/retro.py`: `_workarounds()` and `_restored()`.** Check that they only read git, and keep `unknown` apart from `outside`.
- **`scripts/closing.py`** (sensitive) changes only docstrings, in `_lead_line()` and `measure_change()`.
- **Published interfaces, all already approved in the spec's *Contracts touched***:
  - the run record format: `train` added to 174's ejection row;
  - `retro`'s output: the new `simplicity.workarounds` block;
  - `.sdlc/REVIEW.md`: the doc-claim bullet;
  - the eject and stop output's `problems` entry, from R5.

**Release impact**

- IMPACT: minor — `retro` now reports `simplicity.workarounds`, and the train's ejection rows carry `train`. Both are additive, so someone holding the previous release can newly see these counts and has nothing to change.

**Undone items**

- UNDONE: `/sdlc:retro`'s passes don't read `simplicity.workarounds` yet: its process pass could turn an `outside` or `restored` row into a seed. The report renders it with S14. → seed: retro's process pass seeds from workaround rows
