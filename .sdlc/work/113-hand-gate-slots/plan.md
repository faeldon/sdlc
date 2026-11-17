---
id: 113
slug: hand-gate-slots
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 113 — The hand gate shares the factory's gate slots · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: beside the hand gate's copies, add the slot copies (`SLOT_NAME`, `SLOT_POLL`,
  `FACTORY_CONFIG`, `GATE_JOBS_DEFAULT`), `SLOT_WAIT`, `SlotTimeout`, `_gate_jobs_at()`,
  `_try_lock()`, `_wait_text()` and `_hand_slot()` (after `factory.py`'s `gate_slot()`, plus a
  deadline). `sdlc.py`'s own `_unlock()`, which `_main_lock()` uses, already is the factory's, so
  it is reused rather than copied. `cmd_gate()` takes a slot when `factory_enabled(home)` is true, moving the build's
  hashing and the timed run inside the `with`, and adds `waited` and `slot` to its summary.
  Reuses `_git()`, `_config_at()`'s way of reading the base branch, `factory_enabled()`,
  `_refused()`.
- `tests/test_hand_gate.py`: R1, R3, R4, R5, R7, R8, R9 tests.
- `tests/test_factory.py`: R2's test.
- `plugins/factory/scripts/factory.py`: the slot comment and module docstring say `sdlc.py gate`
  takes the same lock files (no code change).
- `docs/REFERENCE.md` (*The gate, run by hand*), `plugins/factory/README.md` (*One gate at a time*,
  *Mechanism*): R10.
- `AGENTS.md`: the factory paragraph names the one key and the slot files `sdlc` now reads, as the
  person approved (intent's open questions).

## Work order

1. **Copies and `gate_jobs`**: the constants and `_gate_jobs_at()`, with R8's and R3's value
   tests (red: attributes missing).
2. **The shared slot in `cmd_gate()`**: `_try_lock`, `_unlock`, `_hand_slot`, wired in behind
   `factory_enabled`. R1 (both `gate_jobs` 1 and 2), R5, R6's summary fields, R9.
3. **The give-up**: `SlotTimeout` and the refusal; R4's test.
4. **The other direction and the kill**: R2 in `tests/test_factory.py`, R7 in
   `tests/test_hand_gate.py` (both pass on the code of slice 2; written to fail if the lock files'
   names or byte drift).
5. **Docs**: R10 and AGENTS.md; then `./check.sh`.

## Tests

- R1, R3 (the `gate_jobs = 2` case), R6: `test_a_hand_gate_waits_for_a_factory_gates_slot`
  (parametrized on `gate_jobs`): a child holds slot 0 through `factory.gate_slot()` and stamps
  when it lets go; the hand gate's check stamps when it starts.
- R2: `test_a_factory_gate_waits_for_a_hand_gates_slot` (`tests/test_factory.py`): a child holds
  slot 0 through `sdlc._hand_slot()`; `factory.py gate` says it waits and `waited ≥ 0.5`.
- R3: `test_the_hand_gate_reads_gate_jobs_as_the_factory_does`.
- R4: `test_a_hand_gate_gives_up_after_its_wait_and_records_nothing`.
- R5: `test_without_the_factory_the_hand_gate_takes_no_slot`.
- R7: `test_a_killed_hand_gate_frees_its_slot` (`portable`).
- R8: `test_the_slot_copies_are_the_factorys` (`portable`).
- R9: `test_new_claims_a_number_while_a_hand_gate_waits`.
- R10: checked at review.

## Rollback

`git revert` undoes it all. Lock files a hand gate created in the git common dir
(`sdlc-factory-gate-<k>.lock`) stay, as the factory's do; they are empty and hold nothing, and
`rm "$(git rev-parse --git-common-dir)"/sdlc-factory-gate-*.lock` removes them while no gate runs.
