DECISION: READY

**Why.** All four round-1 reviewers (code, test, security, behaviour) passed in the first round. The test reviewer matched each of R1–R10 to a test that fails without it. The gate record is `GATE: PASS`: the first attempt failed only on DNS errors in `tests/test_adoption.py` and one board-browser test that passed alone, and the second attempt passed 3163 tests with ruff and `validate --strict` clean. The one departure from the spec is the wider `FIX_RE`. `plan.md` explains it, the reviewers accepted it, and it is needed for R6's "lines that disagree" refusal to hold. Nothing in the rounds suggests the spec was wrong.

**Open items.** There are no unresolved CHANGE findings. Three nits are recorded in `findings.md`:
- F1 (code): the refusal message at `landing.py:1420` is long and repeats `FIX: ALREADY MADE`.
- F2 (security): `taken_lines()` treats any indented line after the marker as part of it, so an indented sub-bullet naming an id it leaves out would retire that nit.
- F3 (test): the `MADE` and `ALREADY` constants are defined mid-file in `tests/test_land.py`, and `tests/test_train.py` defines a second `MADE`.

**Decisions to confirm.**
- SETTLED: D1: spec R6 requires refusing a report whose `FIX:` lines disagree, which the design's regex (it matches only `ALREADY MADE`) can never detect. `plan.md` records the departure and why. The code checks the answer against `FIX_MADE`. The extended `test_a_fix_commit_needs_an_ask` covers the disagreeing case. The test, code and security reviews in round 1 each endorse it. The line is internal to the builder's report, which only `factory.py` reads, so it is not a published interface.

**For the person at ship.**
1. Look at `cmd_land_fix()` in `plugins/factory/scripts/landing.py` first, especially the new `_not_already_made()` branch. This is a sensitive path. Confirm that an empty diff with no report, no claim or no evidence still refuses, and that `land-<n>.ask.md` is left alone so `LANDING_FIXED` still stops a `by=auto` close.
2. Then look at `taken_lines()` and `TAKEN_RE` in `factory.py`, and weigh F2's continuation-line looseness.
3. Last, read the skill prose in `skills/intent/SKILL.md`, `batch.md` and `skills/spec/SKILL.md`, since it changes how every author names a nit.

**Release impact.**
- IMPACT: minor — factory landings now retire only nits listed on a `Nits taken in:` line, so a host whose intents named nits in prose must now use the line (the shared skills already tell authors to). A landing fix the builder reports as already made now goes on instead of stopping the train. Nothing is removed and no config or template changes.

**Undone items.**
- UNDONE: `tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card` failed in 181's round-1 gate with no error in the record's tail, and passed when rerun alone: likely flaky under a loaded gate. Not this change's code. → seed: Board drawer focus test is flaky under a loaded gate
- UNDONE: `tests/test_adoption.py` needs network (uv fetches PyPI deps for `uv run --script`); a gate with no DNS fails two of its tests. A skip or cache when offline would keep the gate about the code. → seed: Adoption tests fail the gate when offline; skip or cache uv's deps
