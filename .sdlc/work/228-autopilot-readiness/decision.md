DECISION: READY

**Why:** All nine requirements are built, and the reviewers' round 1 verdicts are all PASS. The gate record is green (`4042 passed, 29 skipped`). The test reviewer ran the new tests for R1 to R8 and they passed. The only departures from the spec are the three in `plan.md`'s "Departures from the spec's design" section. Neither the code review nor the test review found a Critical or High issue.

**Open items:**
- NIT (code reviewer): `plugins/factory/README.md:606` has one line past the 100-column wrap. Re-wrap it.
- NIT (code reviewer): `tests/test_autopilot.py:1576` asserts on the literal text `"→ decided by autopilot: keep it"`. Reference a shared constant instead.
- NIT (test reviewer): `tests/test_land.py:2780` only exercises a resumed task, so "the sessions file is as it was" holds trivially. Seed a fresh task and assert the file is not created.

**Decisions to confirm:**
- SETTLED: D1: The code reads `recorded_closes()` twice per agent run, once from `loop_state()` via `intent_closes()` and once from `record_closes()`. The spec's count of one was wrong. `plan.md` explains the departure, `build/round-1.md` and its docstring state it, and the test reviewer accepted it. The test would still catch a third read, and the cost is a small file per agent session.

**For the person at ship:**
- Look first at the `cmd_agent` reorder in `plugins/factory/scripts/factory.py`. `record_closes()` now runs before the sessions-file write and `_record_land()`. The reviewers confirmed the old order failed the new test.
- Look next at `unfenced_lines()`, which `unbuilt_defaults()` now reads builder reports through, and at the docstrings that state why `cmd_answer` and `cmd_decisions` are safe without a lock.
- `autopilot.py` and `landing.py` are untouched. No published interface changed, and nothing is destructive or touches a secret.
- The fenced-case tests and the R6 test failed on the old code. The end-to-end test failed in two scratch edits, one removing `take_markers()` and one stopping `loop_env()` giving the markers back.

- IMPACT: none — this adds tests and fixes two internal records (a refused agent leaves no landing step recorded, and a quoted `- BUILT:` line is no longer counted). The README sentence is clarified, and no output or config changed for a person's runs.

**Undone items:** `notes.md` does not exist and the builder reports nothing left in it, so there are no `- [ ]` items.
