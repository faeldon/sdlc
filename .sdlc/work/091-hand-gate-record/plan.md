---
id: 091
slug: hand-gate-record
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 091 — A gate run by hand leaves a record the board and status read · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: beside `cmd_accept()`, the copied factory constants (`GATE_TIMEOUT`,
  `GATE_TAIL`, `CLONE_MARK`, `HOME_MARK`, `ATTEMPT_VERDICT_RE`, `BUILD_RE`, `SECONDS_RE`), `HAND_GATE`
  (`build/gate.md`), `_hand_paths()`, `_hand_digests()`, `_hand_hash()`, `hand_build()`,
  `_hand_placeholders()` (a copy of `factory.py`'s `_placeholders()`, its checkouts read from
  `git worktree list --porcelain` as `_all_checkouts()` does), `_refused()`, `cmd_gate()`,
  `hand_gate()` and `_gate_attempts()` (`read_gate_file()`'s parsing, `Seconds:` added); `gate` added to
  `OWN_SCRIPT_CMDS`, its parser and dispatch in `main()`; status's loop sets `rec["gate"]` and
  `print_status()` adds `· gate green` / `· gate red`. Reuses `_config_at()`, `trunk_refusal()`,
  `_one_change()`, `checkout_of()`, `_sh()`, `_git()`, `work_rel()`, `STATE_FILES`.
- `scripts/board.py`: `_entry()` sets `gate` on a manual card; `_seen()` reads it after
  `findings.md`; `next_action()` names the red gate first.
- `scripts/board.html`: the `gate green` / `gate red` badge beside `by hand`, built with `h()`.
- `scripts/metrics.py`: a Bash call running `scripts/sdlc.py gate` counts as a `check` event.
- `tests/test_hand_gate.py` (new): R1–R7, R11, R13, R14, and the pins against `factory.py`.
- `tests/test_board.py`: R8–R10.
- `tests/test_metrics.py`: R12's counting; `tests/test_hand_gate.py` R12's `_factory_files()`.
- `docs/REFERENCE.md`: the command, its record, the board's and status's reading (R15).
- `AGENTS.md`: the board paragraph's `_seen()` sentence names the gate record.

## Work order

1. **The build hash** (R6): `_hand_paths()`, `_hand_digests()`, `hand_build()`, tested on a repo
   with a branch: stable, survives a commit, moves on a code edit and a rebase, not on the folder.
2. **The command** (R1–R5, R13, R14): `cmd_gate()` with its refusals, the record, the placeholders,
   the parser; tests for each outcome, each refusal, the base branch's check, and the pins against
   `factory.py` (the same fixture gated by both, line for line).
3. **The reader** (R7): `hand_gate()`, tests for none, current/stale, malformed.
4. **The board** (R8–R10): `_entry()`, `_seen()`, `next_action()`, the badge; tests that gate,
   read, edit and read again; a red gate; a factory card's absent key.
5. **Status** (R11): the line's mark; a test over `print_status`'s output for green, stale, none.
6. **Metrics** (R12): the `check` event; tests.
7. **Docs** (R15), then `./check.sh`.

## Tests

- R1: `test_the_gate_runs_the_base_branchs_check_never_the_checkouts`.
- R2: `test_gate_refuses_and_writes_nothing` (parametrised: no base branch, no check, an
  unparsable base config, no change / ambiguous, a factory folder, another branch checked out).
- R3, R5: `test_the_record_is_the_factorys_shape_line_for_line`,
  `test_the_copies_are_the_factorys`, `test_the_placeholders_are_the_factorys`.
- R4: `test_each_outcome_is_recorded` (pass, fail, timeout, tree changed),
  `test_a_check_that_cannot_start_is_recorded` (didn't run).
- R6: `test_the_build_hash_is_stable_and_survives_committing_the_work`,
  `test_the_build_hash_moves_with_the_code_never_the_change_folder`,
  `test_the_build_hash_moves_on_a_rebase_onto_a_moved_base`.
- R7: `test_hand_gate_reads_none_current_and_stale`,
  `test_a_malformed_record_is_a_problem_never_current`.
- R8–R10: `test_board.py::test_a_green_gate_moves_a_hand_built_card_to_test_until_an_edit`,
  `test_a_red_gate_keeps_the_card_in_build_and_says_so`,
  `test_a_factory_card_never_reads_a_hand_gate`, `test_the_gate_badge_is_built_as_text`.
- R11: `test_status_marks_a_current_gate_only`.
- R12: `test_metrics.py::test_a_hand_gate_is_counted_as_a_check`,
  `test_hand_gate.py::test_a_hand_gate_is_no_factory_file`.
- R13: `test_gate_is_never_pre_approved` (OWN_SCRIPT_CMDS, READ_ONLY, ALLOW_RULES, every skill's
  rules).
- R14: `test_the_record_is_written_with_unix_newlines` (portable).
- R15: `./check.sh`. The spec's by-hand steps can't run on 091 itself: its folder holds `runs/`,
  so R2 refuses it; the board and status tests drive the same steps on fixtures.

## Rollback

`git revert` undoes it all. Not covered: `build/gate.md` records already committed in other
changes' folders, which nothing reads after a revert and which close removes with each folder.
