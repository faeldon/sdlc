DECISION: READY

**Why.** All four round-1 reviewers (code, test, security, behaviour) returned `VERDICT: PASS`, and the gate record `build/round-1.gate.md` is green on `./check.sh` (3191 passed, 29 skipped, both plugins validate). The test reviewer matched R1 to R11 each to a test that fails without it, and R12 (docs) was checked by review. The behaviour check ran the real `retro` and `retro --report` on this repo and got the cost block and both new coverage lines, with the hand-built change counted as missing, not $0. The build followed `plan.md`. Its two additions (`cost_rows()`, and an optional note on `_coverage_line()`) are explained in the builder report, and no reviewer suggested the spec was wrong.

**Open items**
- None. No CHANGE is unresolved. Four nits are on record in `findings.md` as `recorded`:
  - F1: `_cost()` is computed twice per `retro` (raised by code).
  - F2: a run whose call to `claude` returns no figures writes no row, and the `purpose_of()` docstring could say so (raised by code).
  - F3: no `cmd_agent` test checks the `land` field on a landing task's row (raised by test).
  - F4: the stop half of the ejection test asserts only `cause` (raised by test).

**Decisions to confirm**
- No blocking decision is unticked.
- SETTLED: D1: R2 says `decided` is `build` in the run's first round and `rework` after it, which needs a round to compare. `cmd_agent` takes `state["round"] or state["built"]` (`factory.py:4398`) because `loop_state` names no round while it waits on a decision. `test_purpose_by_task_and_round` pins the round mapping, and the code and test reviewers raised nothing against it. This is an internal tagging detail, not scope or policy.
- SETTLED: D2: R9 asks the waste coverage line to "name the untagged count", and R7's `untagged` block is counted in `runs`. The changes those runs belong to are already counted in the line's missing reasons (`runs recorded before purposes N`). The behaviour round's real report shows `172 runs untagged`, and `test_the_report_says_how_far_cost_and_waste_rest` pins it. This is the wording of a report line, not a published interface.

**For the person at ship**
1. `scripts/factory_records.py` `spend_rows()`. Check the session-delta dollars (R5, floored at 0) and the order in which a row is assigned to a part (R6). Every waste figure rests on these two.
2. `factory.py`'s `purpose_of()` and the `cmd_agent` call site around line 4398. Check the rerun rule and the D1 fallback.
3. `landing.py` `_record_ejection()`. Check it is called before `_amend_record()` in both `_train_eject()` and `_train_stop()`.
4. `retro.py` `_cost()`. Check that `cost.changes` is dropped without `--metrics`.

**The release impact you propose**
- IMPACT: minor — a host's `retro` JSON gains a `cost` block (cost per landed change, waste share, spend by role and model) and its report gains two coverage lines. Factory rows gain `purpose`, `task` and `round`/`land` fields, and ejections are now recorded. These are new capabilities; existing rows and readers keep working unchanged.

**Each undone item's disposition**
- None. There is no `notes.md`, and the builder added nothing to it.
