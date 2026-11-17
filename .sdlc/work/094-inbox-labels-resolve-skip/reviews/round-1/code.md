VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:1546 (`verdict_mend()`, with `_task`'s mend branch near line 1753): the once-only mend lives in the build skill's prose, not in the script. After a reviewer's preamble is mended, a second preamble reply still gets `way: mend` from `loop_state()`. Nothing records that the role was already mended, so a rerun of `/sdlc-factory:build` mends it again. The intent's outcome says "a second such reply stops as today", and AGENTS.md now says "once". Fix: write a per-role mend marker in the run folder (for example `runs/<role>.mended`) when `cmd_agent` writes a mend reply. Then `loop_state()` treats a role that is already marked as `rerun`, not `mend`, and `cmd_agent` refuses a second mend for it. Add a test that goes preamble → mend → preamble again → `way: rerun` and a refused second mend. The builder's evidence mend has the same gap today; the same marker covers it.

## Notes

- Optional: `_task`'s mend returns the verdict prompt only (factory.py near line 1755). A `behaviour` reply that is missing both its verdict line and `## Evidence` gets just the verdict mend, and the evidence stop survives. The second mend is then refused by the once rule, so it stops safely rather than wrongly. Consider having `VERDICT_MEND` also ask for evidence when it's owed.
- Optional: D3 (an empty aside commit is skipped, not undone). `_go_on` (sdlc.py near line 3456) takes the generic skip path, and the aside itself is never tested on that path. `test_resolve_skips_a_commit_the_base_already_holds` only covers a non-empty aside. The docstring's claim that the outcome is the same as undoing it holds on reading: the index equals HEAD, so `finish()` has nothing to put back. A test for the empty-aside case would make that checkable. D3 stays the person's to confirm, since it departs from Outcome 3's literal "never skipped".
- Nit: plugins/factory/skills/build/SKILL.md, the `way` sentence, has a dangling `with` before a line break, and reads oddly as wrapped.
- Nit: AGENTS.md's changed paragraph wraps unevenly around `checks.md`, and its "once" should match whatever the CHANGE above settles.
- Done well: `_as_written()` compares entries without the resolved `after`, and the test covers both a neighbour's retirement (no `Update`) and a real edit to `After:` (still an `Update`). `_no_verdict()` keeps the problem text in one place. `preamble()` is pure and read-only, and the end-to-end test takes a preamble reply through the mend to an `approve` the loop reads. D1 and D2 are implemented as their defaults say.

## What I ran

- `pytest -q -n auto` on `tests/test_sdlc.py`, `test_bugs.py`, `test_factory.py` and `test_skills.py`, with `-p no:cacheprovider` and `PYTHONDONTWRITEBYTECODE=1`: 731 passed.
- `ruff check --no-cache .`: passed. `ruff format --no-cache --check .`: passed.
- I did not run `./check.sh` in full, so `claude plugin validate --strict` and `test_adoption`/`test_windows` are unverified here.
- I did not run the empty-aside scenario. The note above on the aside is from reading `_go_on` and `finish()`, not from a test.
