# Plan

> Tier 2, from `spec.md`'s R1–R18. Round 1 built 31–33 before the spec existed; this plan keeps
> what the spec kept of it and says what each slice adds.

## Files to change

- `plugins/factory/scripts/factory.py`:
  - **Kept from round 1 (R1–R5, R7–R9):** `_dirty()`, the raw `-z` status; `_amend_record()`, the
    one amend, guarded to a `HEAD` carrying `Sdlc-Landed:` and refusing any path outside the
    folder, called by `cmd_land_close()` and by `cmd_land()` on `stage: shipped` before `base`;
    `NIT_RE`, `named_nits()`, `retire_nits()` (after ship succeeds, then staged);
    `land_message(..., nits)`'s `Retired nits:` paragraph.
  - **R6:** `named_nits()` reads only intent.md's `## Approach` and spec.md's `## Requirements`,
    each to the next `## ` heading (a new `_section(text, heading)`).
  - **R8:** `land`'s JSON always carries `retired_nits`, `[]` when none.
  - **R12:** `land_verdict(root, folder, cfg, n, settled=False)` lifted out of
    `cmd_land_verdicts()`, which emits it for `land_round(folder)` unchanged. `settled=True` takes
    round `n`'s gate as its last attempt's verdict whatever `HEAD` is now: see R11 below.
  - **R10:** `cmd_resolve(cont=True)` writes the marker as `land-<n>\n<files>\n`.
  - **R11, R13:** `resolution_signals(root, folder, cfg)`: the landing one (marker's round, `pass`
    from `land_verdict(..., settled=True)`, a roundless marker always a signal) and the
    `conflicts.md` one (each file's hash now against the newest complete round's snapshot, or
    always when there is none). `land_signals()` takes its `root` as now (`worktree`) and calls it
    in place of the bare `is_file()`.
  - **R14:** `resolved_files(folder)`, the copy of `sdlc.py`'s `conflicts_resolved()`.
  - **R15:** `cmd_land_close()` reads `HEAD`'s `Sdlc-Landed:`; on `by=auto` it refuses while the
    landing resolution is a signal. Checked before `_amend_record()`, which moves `HEAD`.
  - **R17:** the docstrings of `land_signals()` and `cmd_resolve()`.
- `plugins/factory/skills/land/SKILL.md` (Step 1's signals, Step 3.1 as round 1 left it, Step 3.3's
  stop removed: R16, R17) and `plugins/factory/README.md`'s signal list (R17).
- `tests/test_land.py`.

Reused: `land_round()`, `_rounds_at_depth()`, `read_snapshot()`, `_tree_hashes()`, `_base()`,
`read_verified()`, `_land_gate_state()`, `FENCE_RE`, `find_change()`.

**Why `settled`.** The spec says a later clean landing round leaves the marker's round's pass
standing. `_land_gate_state()` counts a gate attempt only when it ran on `HEAD` as it is now, and
`HEAD` moves after the review passed: the second `land`'s amend (R3) and any later rebase. Read
for the current round, that staleness is right (`land-verdicts` must gate the change as it now
stands, and keeps doing so: R12). Read for R11, it would turn a passed round back into a signal
the moment the landing's own record is amended in. So R11 reads the round's gate as its last
attempt's verdict: red stays red, a pass stays a pass, and a round with no attempt (when the base
names a check) is not passed.

## Work order

Each slice: its test seen failing, then the code, then `test_land.py` green.

1. **R2.** `test_a_landings_record_never_takes_in_a_path_outside_its_folder`: an untracked file at
   the root; the second `land` and `land --close` both refuse naming it, and `HEAD` is unchanged.
   Already true in code: seen failing with the stray check taken out.
2. **R6, R8.** The 32 test gains an id named only in the Problem, and asserts `retired_nits`; red
   on round 1's whole-file read. Then `_section()`.
3. **R7.** `test_a_refused_step_lands_nothing_of_that_change` gains a register with a named nit,
   compared byte for byte after the refusal.
4. **R14.** `resolved_files()` and its pin test.
5. **R12.** `land_verdict()` lifted out; every `land-verdicts` test unedited.
6. **R10, R11.** The batch test asserts the marker's first line and, after `pass`, no signal;
   `test_a_landing_resolution_counts_until_its_review_passes`. Then the marker, `settled` and
   the landing half of `resolution_signals()`.
7. **R13.** `test_a_resolution_the_build_reviewed_is_no_signal_and_one_after_it_is`. Then the
   `conflicts.md` half.
8. **R15.** `test_an_auto_landing_never_closes_over_a_resolution_no_review_passed`. Then the check
   in `cmd_land_close()`.
9. **R16, R17.** The skill and the README; `preflight 097` for the cases' scope.

## Tests

- R1: `test_land_close_reads_a_modified_first_path_in_the_folder_as_the_folders`.
- R2: `test_a_landings_record_never_takes_in_a_path_outside_its_folder`.
- R3, R5: `test_a_second_land_after_main_moves_rebases_with_the_first_record_amended_in`.
- R4: `test_a_record_is_never_amended_into_a_commit_the_landing_didnt_make`.
- R6, R8: `test_a_landing_retires_the_nits_its_intent_names`.
- R7: `test_a_refused_step_lands_nothing_of_that_change`, extended.
- R9: `test_the_landings_nits_are_the_ones_sdlc_reads`.
- R10, R11: `test_a_batch_lands_in_order_and_a_conflict_is_resolved_reviewed_and_closed`, extended;
  `test_a_landing_resolution_counts_until_its_review_passes`, which also moves `HEAD` after the
  pass (the `settled` read).
- R12: the existing `land-verdicts` tests, unedited.
- R13: `test_a_resolution_the_build_reviewed_is_no_signal_and_one_after_it_is`.
- R14: `test_the_landings_resolutions_are_the_ones_sdlc_reads`.
- R15: `test_an_auto_landing_never_closes_over_a_resolution_no_review_passed`.
- R16, R17: skill text, read by the review; R18: `./check.sh`.

## Rollback

`git revert` undoes it all. A nit a landing retired returns to the register with the revert of
that change's commit. A `runs/land-resolved` written in the new shape by a run before the revert
is read by the old code as existing, which is all it read: a signal, as before.
