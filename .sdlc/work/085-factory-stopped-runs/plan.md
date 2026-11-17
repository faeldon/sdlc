---
id: 085
slug: factory-stopped-runs
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 085 — A stopped factory run says so, and how to move it on · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: `STOPPED`, `STOPPED_RE`, `NEXT_RE`, `PROBLEM_RE` beside
  `COSTS`; `WAYS` (way → sentence template); `stop_text(change, way, problems)`; `loop_state()`
  keeps the evidence problems apart as it builds `problems` and sets `out["way"]` on a stop;
  `cmd_verdicts(root, ident, head, record=False)` writes or removes `runs/stopped.md` from the
  same `out` it prints; `--record` on the `verdicts` parser, refused without `--head`; module and
  `cmd_verdicts` docstrings. Reuses `find_change()`, `emit()`, `loop_state()` as they are.
- `scripts/board.py`: pinned copies `STOPPED_RE`, `NEXT_RE`, `PROBLEM_RE`, `STOPPED`; `_factory()`
  reads the record into `stopped` (None without one; an unreadable one is a `problems` line);
  `next_action()` and `column()` act on it at `stage: build` only.
- `scripts/board.html`: one flag per stop problem; the Needs you column's `who`.
- `scripts/sdlc.py`: `FACTORY_STOPPED_RE`, `FACTORY_NEXT_RE`, `FACTORY_PROBLEM_RE`,
  `FACTORY_STOPPED` beside `FACTORY_KEPT_RE`; `factory_stop(folder)`, never raising; status's
  branch of `main()` sets `rec["stopped"]` for an open change at `stage: build`; `print_status()`
  marks the line `· stopped, touched <ago>` and prints `⚠`/`→` lines under the title, each
  problem cut to `STATUS_WIDTH` (100) by `_cut()`. An unreadable record is a stop whose one
  problem says so, its `→` "read runs/stopped.md".
- `plugins/factory/skills/build/SKILL.md`: Step 2's `verdicts … --record`; Step 1 names
  `runs/stopped.md`; the `stop` step says the record carries the problems and the way on, and the
  supervisor never writes, edits or deletes it.
- `skills/status/SKILL.md`: a stopped line is never in flight nor merely quiet; recommended at
  rule 3 with its own `→` step.
- `plugins/factory/README.md`: the file in the folder listing.
- `docs/REFERENCE.md`: the board's Needs you, and the status line.
- `AGENTS.md`: the two sentences of the spec's Contracts touched 1 and 2.
- Tests: `tests/test_factory.py` (R1–R5, R13, R14), `tests/test_board.py` (R6–R9, R11),
  `tests/test_metrics.py` pin (R11), `tests/test_next_up.py` (R10).

## Work order

1. **The record, in `factory.py`.** Tests first: record writes/removes, word-for-word agreement,
   no write without the flag, refusal without `--head`, a way for each stop kind, a stale record
   never stops the loop, `ready` leaves a stopped run out. Then `way`, `stop_text()`, `--record`.
2. **The board reads it.** Tests from 078's round-1 files and a record made with
   `factory.stop_text()`: Needs you with flags and the record's sentence; an unreadable record;
   only at `build`; a resumed run back in Build; the pin test extended. Then `board.py`, the page.
3. **Status reads it.** Test on the status line; the metrics pin extended. Then `sdlc.py`.
4. **The supervisor and the docs.** Test that the skill's `verdicts` call has `--record`; then the
   skill, the status skill, README, REFERENCE, AGENTS.md, docstrings. `./check.sh`.

## Tests

- R1 `test_record_writes_a_stop_and_removes_it_once_clear`; R2 `test_the_record_is_verdicts_own_reading`;
  R3 `test_verdicts_alone_writes_nothing`, `test_record_without_a_head_is_refused`;
  R4 `test_a_stop_names_its_way` (no verdict, HEAD moved, missing evidence) and
  `test_a_third_red_gate_names_rerun`, apart and unmarked since its gate runs `sh`;
  `test_a_problem_spanning_lines_is_one_line_of_the_record` for `stop_text()`'s one-line rule;
  R5 `test_a_stale_record_never_stops_the_loop`; R13 `test_ready_leaves_a_stopped_run_out`;
  R14 `test_the_supervisor_records_each_reading` — all in `tests/test_factory.py`.
- R6 `test_a_stopped_run_needs_the_person`; R7 `test_an_unreadable_stop_record_is_a_problem`;
  R8 `test_a_stop_record_counts_only_at_build`; R9 `test_a_resumed_run_goes_back_to_build` and the
  existing board tests unchanged; R11 `test_the_factory_parsing_is_a_pinned_copy` extended — in
  `tests/test_board.py`; R11 also `test_sdlcs_copies_of_the_factorys_patterns_match_its_own`.
- R10 `tests/test_next_up.py::test_a_stopped_factory_run_is_marked_on_its_status_line`.
- R12 the board's existing no-write and route tests; no new `subprocess` in the core.
- R16 `./check.sh`, new tests that touch no shell fake marked `portable`.

## Rollback

`git revert` undoes all of it. Not covered: a `runs/stopped.md` a supervisor already wrote in an
open change's folder. It is inert without the readers (nothing in the loop reads it) and goes with
the folder at close; delete it by hand (`rm .sdlc/work/NNN-slug/runs/stopped.md`) if wanted.
