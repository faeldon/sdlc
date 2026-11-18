# 141 — Plan

> Stage 3: how the change is built, written after reading the code. A Tier 1 change, so the
> intent's Approach is the spec; this plan exists because the change crosses `board.py`,
> `board.html`, `factory.py` and `sdlc.py`.

## Files to change

- `scripts/board.py`
  - `_on_board()`: keep a shipped or dropped folder whose branch a stopped rebase has detached
    (`sdlc._change_trees()` minus `sdlc.worktrees()`, the set `state()` already computes as
    `rebasing`), beside what `sdlc.ready_to_close()` lists.
  - `LAND_AT` / `LAND_LABEL`: `checks` and `cases` at the `ship` position, labelled by name.
  - `_entry()`: a `land_stop` field (`{"after", "problems"}`) from a stopped landing's progress,
    read before `sdlc.needs_of(entry)`.
  - `column()`: `needs` before the `close` column, so a stopped landing on a shipped card is
    Needs you; the docstring says so.
  - `next_action()`: the build-stage decision line names where the person answers.
  - `read_step()` / `_progress()`: the step record's `- STUCK:` and `- UNTESTABLE:` lines, as
    `progress["early"]`, and the `approve` step's label naming them.
  - Pinned copies: `STUCK_RE`, `UNTESTABLE_RE`.
- `scripts/board.html`
  - `roundRow()`: `B${r.round}`; `progressRow()`: `B${p.round}`, landing rounds stay `L${…}`.
  - `progressRow()`: a flag per early-stop line (`stopped early: …`).
  - The `landing-stopped` class and its style go: a stopped landing is in Needs you, whose
    style it takes.
- `plugins/factory/scripts/factory.py`
  - `LAND_STEPS` gains `checks` and `cases`; `cmd_accept()` records `checks` and `cmd_cases()`
    `cases` through `_record_land()`, before the landing's commit (`_before_commit()`, `stage:
    test`) only: after a rebase the checks run inside the gate's step.
  - `_land_refused()` and `_close_stopped()` record the plain line, then the raw text; every
    caller passes a plain line: `_amend_plain()` for `_amend_record()`'s four whys, texts of
    their own for the two `landed by=auto` stops and the two `resolve` stops. `_record_move()`'s
    way on names `/sdlc:close`, since the change is committed by then.
  - `step_text()` / `read_step()`: `- STUCK:` and `- UNTESTABLE:` lines from `verdicts`'
    `stuck` and `untestable`; `stop_text()` takes the same and writes them under the problems.
- `scripts/sdlc.py`
  - `needs_of()`: `landing stopped at <step>` at `test` or `shipped` from a `land_stop` field,
    before the closed-change return.
  - `factory_land_stop()`: `runs/land-step.md`'s stop, with `FACTORY_LAND_STEP` and
    `FACTORY_AFTER_RE` (copies, pinned), for `status`: open changes at `test`, and the ready-to-
    close list, which `■ What needs me` then includes.
- `docs/REFERENCE.md` (the board and status paragraphs), `plugins/factory/README.md` (the
  `accept`/`cases` line).
- Tests: `tests/test_board.py`, `tests/test_land.py`, `tests/test_factory.py`,
  `tests/test_sdlc.py`.

Reused, not re-derived: `sdlc._change_trees()`, `sdlc.worktrees()`, `_record_land()`,
`land_step_text()`, `step_text()`, `early_stop()`'s output in `loop_state()`, `needs_of()`.

## Work order

1. **A shipped change mid-rebase keeps its card.** Test: a shipped landing at `resolve` whose
   worktree's rebase is stopped is on the board, `rebasing`, on the landing track. Code:
   `_on_board()`.
2. **`accept` and `cases` record a step.** Tests: `cmd_accept`/`cmd_cases` (with `_sdlc`
   stubbed) write `checks`/`cases` at `stage: test` and leave the record alone after; the board's
   track shows each at the `ship` position, labelled. Code: `LAND_STEPS`, the two commands,
   `LAND_AT`, `LAND_LABEL`.
3. **A stopped landing needs the person.** Tests: `needs_of()` with `land_stop` at each stage; the
   board's column for a stop at `test` and at `shipped`; `status`'s `■ What needs me` lists a
   shipped change whose landing stopped; the pinned copy of the record's reading in `sdlc.py`.
   Code: `needs_of()`, `factory_land_stop()`, `cmd_status`/`print_status`, `_entry()`, `column()`,
   the page's class.
4. **Plain stop lines.** Tests: `_amend_plain()` covers each of `_amend_record()`'s whys and names
   the way on; `_land_refused()` records plain then raw; the `by=auto` and `resolve` stops carry a
   plain line. Code: `factory.py`.
5. **An early stop is shown.** Tests: `verdicts --record` on a run kept twice writes `- STUCK:`
   lines `read_step()` reads back (board's copy pinned); the card's `approve` step says so with the
   reasons as flags; `stop_text()` carries them. Code: `step_text()`, `read_step()`, `stop_text()`,
   `cmd_verdicts`, `_progress()`, the page.
6. **The decision line.** Test: the build-stage text names the `/sdlc-factory:build` session.
   Code: `next_action()`; `PRECEDENCE`/`BOTH` updated.
7. **Labels.** Test: the page labels build rounds `B`, landing rounds `L`, never `R`. Code: two
   template strings.
8. Docs, gate.

## Tests

| Outcome | Test |
| --- | --- |
| Rebasing shipped card stays | `test_a_shipped_change_whose_landing_rebase_is_stopped_keeps_its_card` (board) |
| `accept`/`cases` record a step | `test_accept_and_cases_record_their_landing_step` (land); `LANDS["checks"]`, `LANDS["cases"]` (board) |
| Stop → Needs you | `test_a_landing_stop_needs_the_person` (sdlc), `test_a_stopped_landing_is_in_needs_you` (board, replacing 133's `…drops_the_ready_look`), `test_status_lists_a_stopped_landing_under_what_needs_me` (board), `test_the_landing_stop_is_read_as_status_reads_it` (board) |
| Way on names close on a shipped card | existing `test_a_landing_card_names_the_landing_not_close`, `BOTH` |
| Plain stop lines | `test_every_landing_stop_has_a_plain_line_over_its_raw_text` (land); 133's `…records_plain_words` and the resolve test now expect the raw text under the plain line |
| Early stop shown | `test_record_writes_an_early_stops_reason` (factory), `test_an_early_stop_shows_on_the_card` (board), `test_the_step_record_is_a_pinned_copy` extended |
| Decision line | `PRECEDENCE`, `test_a_card_with_a_problem_and_a_decision_names_both` |
| B/L labels | `test_rounds_are_labelled_b_and_landings_l` (board) |

## Rollback

`git revert` undoes everything: the change writes no data outside the repo and publishes
nothing. A `runs/land-step.md` or `runs/step.md` written with the new lines by a landing or run
that happens before a revert is read by the older code as it was: unknown lines are skipped, and
a `checks`/`cases` step the older board doesn't know makes its track `None`, a card without a
track, never an error.
