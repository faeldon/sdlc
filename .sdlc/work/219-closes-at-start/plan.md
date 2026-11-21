# 219 — Plan

> Tier 1, but it touches three files, so it gets a plan. The intent's Approach is the spec.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `_vouch()`: its locked append split out as `_append_ledger(root, line)`, so the new line is
    appended under the same `RECORDS_LOCK`, the same way.
  - New `_closes_line(change, value)`: the ledger's new row, `{"change": ..., "closes": ...}`. It
    has no `record`/`sha256`, so `vouched()` (and core's `vouched_in()`, which compare a whole
    row) never read it as vouching for a record: the format is extended, not redefined.
  - New `recorded_closes(folder)`: every `closes` value the ledger holds for the change, in order.
  - New `record_closes(root, folder)`: appends the intent's `closes:` once (skipped when that
    value is already recorded, and when the intent has none). Raises OSError as `_vouch()` does.
  - `intent_closes(folder)`: the union of `recorded_closes()` and the working copy's value. With
    nothing recorded, or nothing the working copy lacks, it returns the working copy's text as
    today; otherwise the union as `[a, b]`, the recorded issues first.
  - `cmd_start()`: once there are no refusals, `record_closes()`; a failure is a refusal.
  - `cmd_agent()`: `record_closes()` once nothing is left to refuse, before `claude` runs, since
    autopilot never runs `start` (see the decision in the report).
- `plugins/factory/scripts/landing.py` `land_signals()`: the `issue` signal fires on preflight's
  `closes` or on `factory.intent_closes(folder)`, since preflight reads the branch's own intent.
- `plugins/factory/README.md`: the records-ledger paragraph says it also records `closes:`.
- `tests/test_factory_decisions.py`: the tests below.

Reused: `frontmatter()`, `_slot_dir()`, `_try_lock()`/`_unlock()`, `no_confirm_why()`.

Core (`factory_records.py`, the board, `status`) doesn't read the new line, so it has no pinned
copy: the factory's alone (the intent's second open question).

## Work order

1. Record and union: `record_closes()`, `recorded_closes()`, `intent_closes()`, the call in
   `cmd_start()`; test: start, drop `closes:`, `no_confirm_why()` and `land_signals()` still name it.
2. The landing's signal reads the union.
3. The agent call records too; test: an agent run with no `start` records it.

## Tests

- `test_closes_recorded_at_start_outlives_an_edit`: Outcome 1–3 (start records once, the union
  keeps a dropped issue and adds a new one, `no_confirm_why()` and `land-check`'s `issue` signal
  still fire).
- `test_a_change_closing_nothing_records_nothing`: the constraint that a change with no `closes:`
  writes nothing new.
- `test_an_agent_run_records_closes_without_start`: the autopilot path.

## Rollback

`git revert` undoes the code. The ledger's `closes` lines stay in the git common dir; nothing
reads them once reverted, and `vouched()` never matched them.
