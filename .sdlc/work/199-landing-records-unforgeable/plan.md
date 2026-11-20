---
id: 199
slug: landing-records-unforgeable
kind: plan
created: 2026-11-20
updated: 2026-11-20
---

# 199 — Landing records an agent in the change's folder can't forge · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: beside `read_gate_file()`, `RECORDS_LEDGER`,
  `RECORDS_LOCK`, `RECORDS_LOCK_WAIT`, `RECORD_GLOBS`, `_record_digest()`, `_ledger_line()`,
  `_vouch()` (lock through the existing `_try_lock()`/`_unlock()`, the dir from `_slot_dir()`),
  `vouched()`, `_unvouched_refusal()`. `cmd_gate()` and `cmd_accept()`: refuse on an
  unvouched record before `_record_land()` or any run (R7); `_vouch()` the new text, then write
  it (R1). `hand_gate_state()`: `green` needs `vouched()` (R6).
- `plugins/factory/scripts/landing.py`: `forged_records()` (here, not in `factory.py`: only the
  landing calls it, `test_the_line_between_script_and_module_holds`); `cmd_land()` refuses on
  it before any write
  (R3); `land_verdict()` adds a stop problem for an unvouched land gate or accept record (R4);
  `_read_gates()`/`_read_builds()` return the unvouched file, and `_train_gate()`/`_train_build()`
  name `stop` with it (R5).
- `scripts/factory_records.py`: core's copies `RECORDS_LEDGER`, `RECORDS_LOCK` (pinned by
  `test_every_shared_name_is_the_factorys`), `record_digest()`, `ledger_line()`, `vouched_in()`:
  pure, no process, reads only the file it is given.
- `scripts/sdlc.py`: `LEDGER_LOCK_WAIT`, `_ledger_dir()`, `_vouch()` (lock with its `_try_lock()`
  and `closing._unlock()`, append `factory_records.ledger_line()`), `_hand_vouched()`; `cmd_gate()` refuses on an unvouched
  `build/gate.md` before the slot or the check, and vouches before writing (R1, R7). `hand_gate()`,
  `needs_of()`, `seen_stage()` untouched (R8).
- No test helper for vouching hand-written records: the spec expected one in `tests/conftest.py`,
  but no existing test reads a hand-written record through a reader that now checks the ledger
  (the board, `status`, retro and metrics read through core, which doesn't), so none was needed.
- `tests/test_records_ledger.py` (new): R1, R2, R9 and the R8 pin.
- `tests/test_land.py`, `tests/test_train.py`, `tests/test_hand_gate.py`,
  the R3–R7 tests.
- Docs (R10): `AGENTS.md` (*The factory*), `docs/REFERENCE.md`, `plugins/factory/README.md`,
  `plugins/factory/skills/land/SKILL.md`.

Departure from the spec's Design: the spec puts core's copies `_vouch()` and `_record_digest()` in
`sdlc.py`. The ledger's name, its hash and its line format go into `factory_records.py` instead,
since AGENTS.md says core's copies of a run's records live there alone and no other core file
names one; only the locked append (`_vouch()`) stays in `sdlc.py`, which owns `_try_lock()`. The
R8 pin compares the lines both writers append for the same record.

## Work order

1. **Ledger in the factory** (R1 for `factory.py gate`/`accept`, R2, R9): `_record_digest`,
   `_vouch`, `vouched`, `forged_records`; the writers vouch before writing. Tests: ledger holds the
   hash after `gate` and `accept`; the R2 cases; two writers at once.
2. **Writers refuse an unvouched record** (R7, factory half): plant a forged attempt, run `gate`
   and `accept` with a marker command; refused, file unchanged, marker absent.
3. **`land` refuses** (R3): hand-written green `land-accept.md` and `round-<N>.gate.md`.
4. **`land_verdict` stops** (R4).
5. **The train stops** (R5).
6. **Hand gate** (R6 in factory, R1/R7 in core, R8 pin): core copies, `sdlc.py gate` vouches.
7. **Existing tests**: run the affected files (none needed a change).
8. **Docs** (R10).

## Tests

- R1: `test_gate_vouches_for_its_record`, `test_accept_vouches_for_its_record`,
  `test_the_hand_gate_vouches_for_its_record`.
- R2: `test_vouched_reads_the_ledger_alone` (byte change, restore, other change, other path,
  missing/garbled ledger), `test_a_crlf_record_stays_vouched` (portable).
- R3: `test_land_refuses_a_hand_written_accept_record`,
  `test_land_refuses_a_hand_written_round_gate`.
- R4: `test_land_verdict_stops_on_a_hand_written_land_gate`.
- R5: `test_train_run_stops_on_a_hand_written_gate`.
- R6: `test_a_hand_written_hand_gate_clears_nothing`.
- R7: `test_no_writer_appends_to_an_unvouched_record` (factory gate, factory accept),
  `test_the_hand_gate_refuses_an_unvouched_record`.
- R8: `test_the_ledger_writer_is_pinned_to_core`; existing pins in `test_modules.py` and
  `test_hand_gate.py` unchanged.
- R9: `test_two_writers_at_once_leave_whole_lines`; `tests/test_windows.py`.
- R10: the acceptance check in `checks.md`, and the docs read at review.

## Rollback

`git revert` undoes the code. It leaves `sdlc-factory-records.jsonl` and
`sdlc-factory-records.lock` in the git common dir, which nothing reads after the revert: remove
them with `rm "$(git rev-parse --git-common-dir)"/sdlc-factory-records.*`.
