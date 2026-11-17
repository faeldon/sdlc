---
id: 088
slug: board-progress
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 088 — The board shows how far each change has got · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `STEP`, `STEP_RE`, `ROUND_RE`, `LIMIT_RE`,
  `REVIEWERS_RE`, `SINCE_RE`, `AFTER_RE` beside `STOPPED`; `step_text()` and `read_step()` beside
  `stop_text()`; `cmd_verdicts(record=True)` writes `runs/step.md` after `stopped.md`'s handling.
  `loop_state()` untouched. `SECONDS_RE` named beside `ATTEMPT_VERDICT_RE` for the gate's
  `Seconds:` line (the board's copy is pinned to it). Module and `cmd_verdicts` docstrings.
- `scripts/board.py`: copies of the record's constants, `REVIEWER_ROLES` (= `factory.REVIEWERS`)
  and `SECONDS_RE`; `_progress()` (the track, the bar's figures, the plan hint), `_step()` (reads
  the record), `_touched()` factored out of `_seen()` (which keeps its behaviour), `_plan_named()`,
  `typical_times()` with its in-memory cache keyed by base-branch tip, `_samples()` (R9 from one
  change's `costs.jsonl` rows and gate seconds). `_entry()` gains `progress` for a factory card
  only; `state()` passes the history table through.
- `scripts/board.html`: `progressRow()` after the round rows: `.track` of six `.step` chips
  (`done`/`current`/`todo`/`paused`), `R<round> of <limit>`, a `.bar`/`.fill` whose width is
  `progress.fraction`, its label, and the `plan: T of N files touched` meta line. Styles for them.
- `scripts/sdlc.py`: `TEMPLATE_READS["plan.md"] = {"headings": ("Files to change",)}`.
- `tests/test_factory.py`: R1–R3 tests.
- `tests/test_board.py`: R4–R11, R13, R14 tests; pins extended (R7).
- `tests/test_setup_lifecycle.py`: R12's override test beside the `TEMPLATE_READS` tests.
- `plugins/factory/skills/build/SKILL.md`: step 2's `--record` sentence names `runs/step.md`.
- `AGENTS.md` (*The board*, *The factory*'s `--record` sentence), `docs/REFERENCE.md` (**The
  board**).

Reused, not re-derived: `sdlc._git`, `sdlc._dirty_paths`, `sdlc.checkout_of`, `sdlc.work_rel`,
`sdlc.DIR_RE`, `sdlc._section`/`_body_of`, `sdlc.is_unfilled`, `sdlc.frontmatter_list`, the
board's own `VERDICT_RE`; `statistics.median`.

## Work order

1. **The record (R1–R3).** Tests in `test_factory.py`, then `step_text()`/`read_step()` and the
   write in `cmd_verdicts`. On `decide`, the record also carries `AFTER: <step>`, the step it
   paused at (taken from the record it replaces), so the board can keep that position (R4).
2. **The track (R4–R7, R14's manual-card assertion).** Board tests over each `next` value, the
   review count, the first-build fallback and the pins; then `_step()` and `_progress()` with
   `elapsed` only.
3. **The estimate (R8–R10).** History built in a repo with `Close` commits whose parent holds
   `costs.jsonl` rows from `factory.record_cost()`; then `typical_times()`, `_samples()`, cache.
4. **The plan hint (R11–R12).** `_touched()` out of `_seen()`, `_plan_named()`, the
   `TEMPLATE_READS` entry and its drift test.
5. **The page (R13).** The bar test, then `progressRow()` and its styles.
6. **Docs (R15) and the gate (R16).** `test_the_board_writes_nothing` over the new inputs (R14).

## Tests

- R1 `test_record_writes_the_step_it_read`; R2
  `test_the_step_record_keeps_its_since_while_the_step_holds`; R3
  `test_the_step_record_never_reaches_the_loop` (`tests/test_factory.py`).
- R4 `test_a_factory_card_shows_its_step_track` (parametrised over every `next`, a decision, a
  stop); R5 `test_reviews_count_up_as_they_land`; R6
  `test_a_first_build_runs_from_its_builder_session`, `test_a_run_without_a_record_has_no_track`;
  R7 `test_the_step_record_is_a_pinned_copy`; R8
  `test_the_estimate_is_capped_and_absent_without_history`; R9
  `test_typical_times_come_from_closed_factory_runs`; R10
  `test_history_is_read_once_per_base_branch_tip`; R11
  `test_the_plan_hint_counts_named_files_the_branch_touched`; R13
  `test_the_bar_is_drawn_from_the_capped_fraction`; R14 `test_the_board_writes_nothing` extended,
  and the manual card's `"progress" not in` assertion (`tests/test_board.py`).
- R12 `test_an_override_plan_without_files_to_change_is_reported`
  (`tests/test_setup_lifecycle.py`).
- Beyond the spec's names: `test_a_decide_record_keeps_the_step_it_paused_at` (the `AFTER:`
  line, R4's paused position), `test_a_decision_or_a_stop_overrides_the_record` (R4's decision
  and stop cases), `test_a_garbled_step_record_is_a_problem` (the design's edge case).
- R15 is prose; R16 is `./check.sh`.
- Manual: the spec's board walk-through (a `step.md` at `review` round 2, two of four reviews in).

## Rollback

`git revert` undoes all of it. What it doesn't: `runs/step.md` files a supervisor already wrote in
open change folders stay there, read by nothing once reverted, and are removed with each change's
folder at close (or by hand: `rm .sdlc/work/*/runs/step.md`). The board's cache is in memory only.
