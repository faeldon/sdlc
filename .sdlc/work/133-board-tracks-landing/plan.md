---
id: 133
slug: board-tracks-landing
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 133 — The board tracks a change through its landing, as it does a build · plan

> Written by the builder after reading `factory.py`'s landing (`cmd_land`, `cmd_land_close`,
> `cmd_resolve`, `cmd_land_verdicts`, `cmd_gate --land`, `cmd_agent`), its step record
> (`read_step`, `step_text`, `_record_step`), and `board.py`'s `_progress`, `step_samples` and
> `history_samples`, with `board.html`'s `progressRow`.

## Files to change

- `plugins/factory/scripts/factory.py`: a landing step record of its own, `runs/land-step.md`
  (`LAND_STEP`, `MOVES_RE`, `read_land_step()`, `land_step_text()`, `_record_land()`), beside
  `runs/step.md`, whose shape and writer stay as they are. Reuse `STEP_RE`, `ROUND_RE`,
  `LIMIT_RE`, `SINCE_RE`, `AFTER_RE`, `PROBLEM_RE`, `_utc_now()`, `land_round()`, `LAND_MOVES`
  and `load_config()`'s `land.moves`. Writers:
  - `land`: `ship` before `sdlc.py ship` stages every path (stage `test`, and the rerun after a
    failed commit), `rebase` before `_amend_record()` on a landing again; so the record always
    goes into the commit, and `sdlc.py base` still finds the tree clean. A refusal after the
    first write records `stop`.
  - `gate --land`: `gate`, before the tree is hashed, so the gate still finds it as it was.
  - `agent` with a landing task: `resolve`, `fix` (land-fix), `review` (land-review), `verify`,
    `mend`, before the session starts. `SINCE:` holds while step and round do, so the reviewers
    started together share one start.
  - `resolve`: `stop` on its refusals; `--continue` stages the record with the costs line, since
    the builder's resolve session writes it mid-rebase. It writes no step of its own: a `clean`
    rebase must leave the tree clean, and `gate --land` records the gate that follows.
  - `land-verdicts --record`: a `stop` with its problems, at the step it stopped after. Without
    `--record` it writes nothing, as now.
  - `land --close`: `close` before `_amend_record()`, so it is in the commit close merges; on
    `moved`, `rebase` with the move counted, before the amend (round 1); `stop`
    on a refusal (the moves bound included).
- `plugins/factory/skills/land/SKILL.md`: `land-verdicts <NNN> --record` (its rule
  `factory.py land-verdicts *` covers it).
- `scripts/board.py`: copies of `LAND_STEP`, `MOVES_RE`, `PROBLEM_RE` and `read_land_step()`;
  `LAND_TRACK = (ship, rebase, gate, review, verify, close)` and `LAND_AT` (`resolve` and `fix`
  sit at rebase as "resolving"/"fixing", `mend` at review as "mending"; `accept` records no
  step); `_progress()` reads `runs/land-step.md` first for a change at `test` or `shipped`
  (`_land_progress()`); `step_samples()` and `history_samples()` add `land-gate`, `land-review`
  and `land-verify` samples (the rows after the approver, and `build/land-*.gate.md`).
- `scripts/board.py` round 1: `next_action()` names a landing under way, and a stopped one's way
  on, above shipped's `/sdlc:close` (pinned in `PRECEDENCE`). A stop's reasons are plain words:
  `_land_refused()` records `plain` when the refusal is a tool's raw output.
- `scripts/board.html`: a stopped landing's card drops the ready look (`.card.landing-stopped`); `progressRow()` labels a landing track (`landing L<n>`, `moves m of k`),
  a `stopped` step state in words and in a dashed style, and the stop's problems as flags.
- `tests/test_land.py`: the landing commands write the record at each step; it ends in the
  commit; a stop records its problems.
- `tests/test_board.py`: the pinned copies; a landing track per step; a stopped landing; landing
  history samples; the fixture holds a landing card.
- `tests/fixtures/board/changes/012-draft-publish/` (new): a change mid-landing, shipped, its
  landing round's review under way.
- `plugins/factory/README.md`, `docs/REFERENCE.md`: the record and the landing track, a line each.

## Work order

1. **The record and `land`'s writes.** `read_land_step`/`land_step_text`/`_record_land`; `land`
   writes `ship`/`rebase` into the commit. Test: after `land`, `HEAD` holds `runs/land-step.md`
   naming the step and the tree is clean.
2. **The rest of the writers**: `gate --land`, `agent`'s landing tasks, `resolve`, `land-verdicts
   --record`, `land --close`. Tests through the existing landing scenarios.
3. **The board reads it**: pinned copy, `_land_progress()`, the column untouched. Tests per step,
   a stop, and that a build record and a decision still read as before.
4. **Timing**: landing samples from history. Test with a closed run's rows after the approver.
5. **The page and the fixture**: `progressRow()`; fixture `012-draft-publish`; the fixture test
   asserts a landing track.
6. **Docs and the skill's `--record`.**

## Tests

- Writer (Outcome, Tests 1), test_land.py: `test_a_landing_records_each_step_it_takes` walks
  land → gate → review → verdicts → close (moved) → land → close, reading `runs/land-step.md`
  and the commit after each; `test_a_resolving_landing_records_the_builder_in_the_rebased_commit`;
  `test_a_stopped_landing_records_why`; `test_a_landing_past_its_moves_records_the_stop`;
  `test_the_landing_step_record_reads_back_what_it_writes`.
- Pinned parser (Tests 2): `test_the_landing_step_record_is_a_pinned_copy` (test_board.py).
- Render (Outcome 1–3, Tests 3): `test_a_landing_card_shows_its_landing_track` per step,
  `test_a_landing_from_ready_to_ship_is_tracked_there`, `test_a_stopped_landing_shows_why_on_its_card`,
  `test_a_landing_record_counts_only_at_a_landing_stage`,
  `test_landing_typical_times_come_from_closed_factory_runs`,
  `test_the_page_labels_a_landing_track_and_says_why_it_stopped`, and the fixture's landing card
  (`test_the_board_fixture_shows_every_card_state`, `test_the_board_fixture_lands_as_the_factory_writes`).

## Rollback

`git revert` undoes it all. Changes landed while it stood keep a `runs/land-step.md` in their
history, which nothing reads once reverted: harmless.
