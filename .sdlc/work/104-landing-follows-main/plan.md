---
id: 104
slug: landing-follows-main
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 104 — The landing follows main and reviews its own fixes · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`:
  - `DEFAULTS["land"]` gains `"moves": 3`. `_land()` validates `moves` as it does `batch`, and its
    warning is reworded.
  - `_behind(root)` (new) counts `rev-list --count HEAD..refs/heads/<base>`, with the base from
    `_base()`.
  - `_record_move(root, folder, cfg)` (new) checks `runs/land-moves` against the bound and appends
    the base tip. It is shared by the check before close and the re-check after a refused close.
  - `cmd_land_close()` checks for a move, records it, amends through `_amend_record()`, and returns
    `moved`. When `sdlc.py close` refuses, it counts the base again.
  - The order differs from the spec's Design: 097's `by=auto` check stays first, as 097 wrote it,
    and the move check comes after it, then the amend. The amend still carries the move's line
    (R2), and 097's code is untouched.
  - `_amend_record()` gains `also=()`, the paths outside the folder it stages and admits.
  - `cmd_land_fix()` (new) has two parts: `--ask R<k>` opens round `land-<n+1>` and writes
    `build/land-<n+1>.ask.md`; `--commit` amends the builder's edits. It gets a `land-fix`
    argparse entry.
  - Round 2 (the person's `R2`, decisions.md): `--ask` takes the id of a ticked
    `- [x] R<k> (person, fix): <words>` line in `decisions.md`, never the words. `FIX_WORDS_RE` and
    `read_fix_words()` read it, as `read_revision()` and `read_restart_words()` read theirs, and
    the command copies the words into the ask file. An id with no such line, unticked or of
    another kind, is refused. The ledger (`LEDGER_RE`, `D<k>` only) reads past the line.
  - `_land_task()` gets a `land-fix` branch, and its `land-review` prompt quotes an ask.
  - `land-fix` is added to `TASKS`, `TASK_ROLE`, `LAND_TASKS` and `RESUMES`.
  - `land_verdict()` wants the run's reviewers when the round has an ask, and adds `fixed`.
  - `land_unreviewed()` (new) compares `_tree_hashes()` with the newest complete build round's
    snapshot. `_changed_paths()` already leaves out the change folders.
  - `land_signals()` gains an `unreviewed` keyword (R13) and the fix signal (R12). The keyword
    defaults to `()`, nothing unreviewed, so 097's callers are unchanged. `None` means no snapshot.
  - `_unreviewed_at_test()` (new) runs `land_unreviewed()` only at `stage: test`, for `cmd_land()`
    and `cmd_land_check()`.
  - `land_ask()` and `land_ask_path()` (new) read the ask. `LANDING_FIXED` is the signal's
    wording.
  - `land_message()` gains `unreviewed` (R14).
  - `cmd_land()` and `cmd_land_check()` compute `land_unreviewed()` at `stage: test`.
  - The `by=auto` check in `cmd_land_close()` also refuses a change fixed at landing.
- `scripts/metrics.py`: `landed_unreviewed(summary, tip)` (new, pure). It takes the branch tip's
  parsed trailers and sets `totals["unreviewed"]` only on a landed change whose tip has the field.
  The module docstring names the field.
- `scripts/sdlc.py`, `measure` (around `tip = metrics.parse_trailers(...)`): reads
  `tip["landed"]["unreviewed"]` and calls the helper inside `finish()`, so the history-only path
  gets it too.
- `plugins/factory/skills/land/SKILL.md`:
  - the `land-fix` rule;
  - `land.moves` read in Step 0;
  - the new WAIT question with four answers;
  - Step 3.4 handles `moved`;
  - a Step 3.5 for a fix the person asked for, which writes the person's words as a ticked
    `(person, fix)` line in the change's `decisions.md` (the skill gains `Write` and `Edit`) and
    passes `--ask R<k>`, as the build skill does for `revise` and `restart`.
- `plugins/factory/README.md`: `moves = 3` in `[land]`, the follow loop, and the fix at landing.
- `docs/REFERENCE.md`, *Metrics*: `unreviewed=` on `Sdlc-Landed` and `Sdlc-Totals`.
- Tests:
  - `tests/test_land.py`: eight new tests. `_ready()` gains `reviewed=True`, which leaves one
    complete, snapshotted build round, as a factory run does (see the decision below).
  - `tests/test_metrics.py`: one new case.
  - `tests/test_skills.py`: `READS_CONFIG["sdlc-factory:land"]` gains `factory.land.moves`.

Reused, never re-derived:
- `_amend_record()` and `_dirty()` (097);
- `_rounds_at_depth()`, `read_snapshot()` and `_tree_hashes()` (as `resolution_signals()` uses
  them);
- `land_round()`, `land_verdict()`, `_land_gate_state()` and `landed_build()`;
- `metrics.parse_trailers()`, which needs no change.

## Work order

1. **The bound's key** (R5's config half): `_land()` and `DEFAULTS`, tested through `load_config`
   on a base branch with `moves = 1` and a change branch with `moves = 10`.
2. **Following main** (R1, R2, R4, R5's loop): `_behind()`, `_record_move()` and the
   `cmd_land_close()` path. The tests:
   - the whole chain (R3);
   - the race with close (R4), with `_sdlc` stubbed;
   - the bound (R5).
3. **The unreviewed record** (R13, R14): `land_unreviewed()`, the signal, and `land_message()`.
   `_ready(reviewed=True)` lands here, because the new signal would otherwise refuse `auto` on
   every 097 fixture. The test is a hand edit after the snapshot.
4. **Measure carries it** (R15): the metrics helper, then the `sdlc.py` call.
5. **A fix at landing** (R8–R12): `cmd_land_fix --ask`, `agent --task land-fix` (with `_claude`
   stubbed), `--commit` with `also`, the depth in `land_verdict()`, and the signal at `land` and
   `land --close`.
6. **The skill and the docs** (R6, R7, R8's prose, R16), then `test_skills.py`.

## Tests

- R1, R2, R3: `test_main_moving_before_close_sends_the_landing_back_to_its_rebase`.
- R4: `test_a_move_racing_close_reads_as_moved`.
- R5:
  - `test_a_landing_stops_after_land_moves_moves`;
  - `test_the_bound_on_following_main_is_the_base_branchs`.
- R6, R7: `tests/test_skills.py` (one WAIT, 2–4 answers, every rule used, `land.moves` read).
- R8, R9, R10, R11: `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth`, and
  `test_a_fix_commit_needs_an_ask` (R10).
- R8 (round 2): `test_a_fix_is_asked_by_its_line_in_decisions_md_never_on_a_command_line`, with
  words holding a quote and `$(`; and `tests/test_skills.py::
  test_the_land_skill_passes_a_fixs_id_never_its_words`.
- R10: `test_a_landings_record_never_takes_in_a_path_outside_its_folder`, unedited.
- R12: `test_a_fix_at_landing_is_never_landed_by_auto_later`.
- R13, R14: `test_a_hand_edit_after_the_approver_is_a_signal_and_recorded`.
- R14: `test_a_landed_commit_says_who_passed_its_gate_and_carries_no_review_count`, unedited.
- R15: `tests/test_metrics.py::test_a_landing_with_unreviewed_paths_carries_them_to_totals`.
- R16: docs. Ship checks them as context docs.

## Rollback

`git revert` of the change's commit covers it all. No data is written outside the repo. A
landing that ran with this code may have left `runs/land-moves` or `build/land-<n>.ask.md` in a
change's folder, which is already committed with that change. They are inert once the code is
reverted, and nothing reads them.
