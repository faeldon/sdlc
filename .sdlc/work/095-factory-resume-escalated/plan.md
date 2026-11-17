---
id: 095
slug: factory-resume-escalated
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 095 — An escalated factory run can be sent back for another build · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: new constants `RESTART_RE`, `WORDS_RE`,
  `RESTART_WORDS_RE`; new readers `restart_path()`, `read_restarts()`, `next_archive()`,
  `reconsider_section()`, `read_restart_words()`; `restart_state()`, shared by `cmd_start()` (its
  `stage: test` branch, read-only) and the new `cmd_restart()` (record, rename, stage, through the
  existing `set_stage()`); `depth()` and `_rounds_at_depth()` take the restart rounds (R8);
  `loop_state()` gets the restart's build branch, counts `exhausted`, `rework` and `limit` from
  the restart (R7) and carries `state["restart"]`; `_task("build")` composes the restart prompt
  (R6); `main()` gains `restart <id> [--words R<n>]`. Reused, not re-derived: `read_decision()`,
  `build_round()`, `read_rounds()`, `set_stage()`, `find_change()`, `frontmatter()`.
- `plugins/factory/skills/build/SKILL.md`: Step 0 (start takes an escalated change), Step 1
  (what to show for a restart), Step 2 (the third wording), Step 3 (`restart` in place of
  `stage`, the `R<n> (person, restart)` line after the yes), the `build` bullet, one new
  `allowed-tools` rule.
- `tests/test_factory.py`: every R-named test of the spec (below).
- `tests/test_board.py`: `test_a_restarted_factory_card_is_in_build_with_its_old_decision_as_a_file`.
- `plugins/factory/README.md`: the folder's files (`decision-<n>.md`,
  `build/round-<N>.restart.md`) and how an ESCALATE goes back to the factory.
- `AGENTS.md`: the factory paragraph, one sentence on `restart`.
- `docs/REFERENCE.md`: the board's Needs-you line now says the ESCALATE is the current
  `decision.md`'s, and that a change sent back keeps it as `decision-<n>.md` and is in Build.
- No change to `scripts/board.py` or `scripts/sdlc.py`: both read `decision.md` alone, and every
  glob of `build/round-*.md` already skips `round-<N>.restart.md` (non-numeric stem).

## Work order

1. **Start reports a restart (R1, R2).** `read_restarts()`, `next_archive()`,
   `reconsider_section()`, `restart_state()`, the `stage: test` branch of `cmd_start()`. Tests
   first: takes an escalated change (tree unchanged), refuses READY / missing / unreadable.
2. **Restart writes (R3, R4).** `cmd_restart()` and its CLI. Tests: archive bytes, numbering
   from 1 and never overwriting, `HEAD` unmoved, a cut-short restart finishing on rerun.
3. **The loop after a restart (R5, R7, R9, R10, R11's `ready`).** `loop_state()`'s restart
   branch and counts, `state["restart"]`. Tests: verdicts names build at R then gate then review,
   the round limit from the restart, the gate's fixes per round, a bad record stops, not ready.
4. **Depth (R8).** `depth()` by position within its run. Test: light stays light, full stays full.
5. **The restart prompt (R6).** `_task("build")` at the restart round, with `--words`. Tests read
   the fake `claude`'s argv.
6. **The board (R11).** Test only: the card is in Build, `decision` null, `decision-1.md` in
   `files` and served by `/file`.
7. **The skill (R12)** and **the docs (R13)**, then `./check.sh` (R14).

## Tests

- R1: `test_start_takes_back_an_escalated_change`
- R2: `test_start_refuses_a_ready_or_unreadable_test_change`; the existing
  `(2, "test", "build", False)` row of `test_start_checks_the_tier_and_stage`
- R3: `test_restart_keeps_the_decision_as_history`,
  `test_restart_numbers_archives_from_one_and_never_overwrites`, `test_restart_moves_no_head`,
  and, added while building, `test_restart_refuses_to_overwrite_an_archive` (the refusal comes
  before any write) and `test_restart_refuses_what_start_refuses` (the shared check)
- R4: `test_a_restart_cut_short_finishes_on_rerun`
- R5: `test_restart_then_verdicts_builds_round_r`
- R6: `test_the_restart_prompt_carries_the_escalation`,
  `test_the_restart_prompt_carries_the_persons_words`
- R7: `test_the_round_limit_counts_from_the_restart`
- R8: `test_a_restarted_light_run_stays_light_and_a_full_one_stays_full`
- R9: `test_a_restart_round_gets_its_own_gate_fixes`
- R10: `test_a_bad_restart_record_stops_the_run`
- R11: `test_a_restarted_change_is_not_ready`; `tests/test_board.py`
  `test_a_restarted_factory_card_is_in_build_with_its_old_decision_as_a_file`
- R12: `tests/test_skills.py` as it stands (rules match commands, one WAIT, the dialog)
- R13: manual — `sdlc.py context` at ship lists nothing left unedited
- R14: `./check.sh`

## As built

- The `restart` object also carries `record` (the record's path in the folder, the one written or
  to be written) and `under_way` (true for a restart cut short), which `restart` uses to only set
  the stage on a rerun (R4).
- `_rounds_at_depth()` reads the restart records, so their problems reach `verdicts` (R10) and
  `run["restart"]` reaches `loop_state()`; `carry` and `land-verdicts`, its other callers,
  discard its problems as before.
- R6 and R11's board test passed as pins: the board needed no code change, as the spec said.

## Rollback

`git revert` covers the code, the skill and the docs. Not covered: a change already restarted in
some worktree keeps its `decision-<n>.md` and `build/round-<R>.restart.md`. Without this code the
old `verdicts` ignores the record and reads no `decision.md`, so it would resume that change's
loop from its files as a plain run; to put such a change back as it was, by hand in its worktree:
`mv decision-<n>.md decision.md`, `rm build/round-<R>.restart.md`, and
`factory.py stage <NNN> test`. Nothing is published or written outside the change's folder.
