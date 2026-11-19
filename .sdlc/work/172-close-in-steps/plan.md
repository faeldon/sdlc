---
id: 172
slug: close-in-steps
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 172 — Close runs as named steps · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/closing.py`: `cmd_close` (lines 708–1076) split into the `_Close` state class,
  `_emit`, `_close_target`, `_close_refusals`, `_close_preview`, `_close_steps`,
  `_run_close_steps` and the eleven `_step_*` functions, each closure's body moved word for word
  with `main` → `c.main` and so on. `_lead_line()` gains `errors`; `measure_change()`'s `finish`
  passes it. Module docstring and `cmd_close`'s docstring name the steps and `_Close` (R13).
  Reused as they are: `_merged_scripts`, `_handoff`, `_push_plan`, `_push`, `_cleanup_plan`,
  `_ff_deletions`, `_reaches`, `_carries_others`, `_branch_register_plan`, `_drop_commit`,
  `_drop_record`, `_close_commit`, `fix_trailers`, `measure_change`, `_main_lock`.
- `scripts/sdlc.py`: the rerun ceiling in `cmd_run_cases` (R9), `import math`.
- `tests/test_archive.py`: `test_close_output_is_unchanged` (R4), written and passing against the
  old code before the move; `test_a_change_opened_after_its_close_says_bad_opened` (R7); one
  assertion added to `test_timing_that_fails_drops_only_its_own_line` (R8).
- `tests/fixtures/close-output.json` (new): R4's pinned reports, commits and trees, recorded from
  the old code.
- `tests/test_modules.py`: R3's names in `CLOSING_NAMES`; `test_close_is_a_sequence_of_named_steps`
  (R1, R2).
- `tests/test_evals.py`: `test_the_rerun_ceiling_keeps_its_last_cent` (R9).
- `tests/test_skills.py`: `test_only_the_named_steps_push` follows the push into `_step_push`.
- `docs/REFERENCE.md`: R14's sentence in §Metrics (ask first: raised as a default).

## Work order

1. **Characterization (R4).** Write `test_close_output_is_unchanged` with its five scenarios and
   the normaliser; record `close-output.json` from the old code; see it pass on the old code.
   Nothing else changes in this slice.
2. **The move (R1–R3, R6, R11–R13).** Red: `test_close_is_a_sequence_of_named_steps` and the new
   `CLOSING_NAMES` entries fail on the old code. Green: move each closure to a top-level
   `_step_*` on `_Close`, then the refusals, preview, step list and loop. The test of slice 1 and
   every close test stay green with no edit.
3. **R8.** Red: the new assertion in `test_timing_that_fails_drops_only_its_own_line`. Green:
   `_lead_line()` gains a last positional `errors` list (positional, so the tests' `lambda *_`
   stand-in still fits); `finish` passes a fresh list and sets `summary["errors"]` only when it
   holds something, so a healthy summary is as before; `_step_measure` copies it into the
   report.
4. **R7.** `test_a_change_opened_after_its_close_says_bad_opened`: expected to pass on the code
   as it is (the nit is a missing test, not a bug); it is seen failing by breaking the check it
   pins, then restored.
5. **R9.** Red: `test_the_rerun_ceiling_keeps_its_last_cent` (0.65 gives `4.34` today). Green:
   `math.floor(round((cap - spent) * 100, 6)) / 100`.
6. **R14.** The REFERENCE sentence.

Departures from the spec's Design, found while building:

- `_Close` is a plain class with an explicit `__init__`, not a `@dataclass`: `closing.py` is
  loaded by path and never put in `sys.modules`, and `dataclass` (with `from __future__ import
  annotations`) looks the class's module up there, so the file fails to load. Raised as a
  default.
- R9's second case: 0.30000000000000004 leaves `4.7` under the old and the new formula alike, so
  the spec's `"4.69"` can't hold. The test pins 0.30000000000000004 → `4.7` (noise ignored) and
  0.305 → `4.69` (a real fraction rounds down). Raised as a default.
- `tests/test_skills.py::test_only_the_named_steps_push` is edited, which R5 doesn't list: it
  required `_push(` to be called only by `cmd_publish`, `cmd_close` and `cmd_release`, matched
  by substring, so R3's `_step_push` (which calls `_push(`, and whose own name holds `_push(`)
  can't pass it. It now matches a call with a word boundary, expects `_step_push` in place of
  `cmd_close`, checks `_step_push` is called only by `_run_close_steps`, and looks for
  `_push_plan(` in `_close_preview`. A planted caller is still caught. Raised as a default.
- R7's test passes on the code as it was (the nit is a missing test); it was seen failing by
  breaking the branch it pins, then restored.

## Tests

- R1, R2: `tests/test_modules.py::test_close_is_a_sequence_of_named_steps`.
- R3: `CLOSING_NAMES` through `test_close_push_and_the_lock_live_in_closing`.
- R4: `tests/test_archive.py::test_close_output_is_unchanged`, five scenarios.
- R5, R6, R11, R12: the existing tests unedited: `test_archive.py`, `test_cleanup.py`,
  `test_push.py`, `test_register_lands.py`, `test_train.py`, `test_land.py`, `test_adoption.py`,
  `test_windows.py` and the rest of the gate.
- R7: `tests/test_archive.py::test_a_change_opened_after_its_close_says_bad_opened`.
- R8: `tests/test_archive.py::test_timing_that_fails_drops_only_its_own_line`.
- R9: `tests/test_evals.py::test_the_rerun_ceiling_keeps_its_last_cent`, with
  `test_a_failed_case_reruns_once_alone`'s `3.75` still holding.
- R10: no code; ship's `entries.md` retires the four nits.
- R13: read in review.

## Rollback

`git revert` of the change's commit undoes all of it: code, tests, fixture and the REFERENCE
sentence. Nothing is written outside the repo, and no trailer, ref or report key changes shape, so
nothing already recorded by a close needs undoing.
