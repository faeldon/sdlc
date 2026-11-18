---
id: 162
slug: lead-time
kind: plan
created: 2026-11-18
updated: 2026-11-19
---

# 162 — Lead time, and where it goes, on every change · plan

> Written by the builder after reading `sdlc.py`'s `cmd_new`/`_stamp`, `closing.py`'s
> `measure_change()` and `cmd_close`'s `measure()`, `metrics.py`'s trailers and events,
> `retro.py`'s `process_views()`/`render_report()`, and `factory.py`'s `record_cost()`,
> `cmd_agent()` and `_record_land()`.

## Files to change

- `scripts/sdlc.py`: `cmd_new()` adds `opened:` to the rendered `intent.md` through a new
  `_with_opened(text, stamp)` and `OPENED_FORMAT`, both above `cmd_new` (the command registry's
  test wants `cli_new` right after it). Lines are edited in place, as `_stamp` does. Nothing else.
- `scripts/metrics.py`: `lead_time()` and `lead_trailer()` beside `trailers()`, reusing
  `_minutes()` and `_pairs()`; the docstring's contract gains both and the `Sdlc-Lead` line.
  `parse_trailers()` needs no change (an unnamed line is `out["lead"] = fields`).
- `scripts/closing.py`: `opened_at(text)` (only close reads it, so it lives here); the run files'
  readers `_timed_rows()` and `_land_sinces()` (with `RUN_TIME_FORMAT`, a copy of the factory's
  `_utc_now()` format, pinned by a test against rows the factory wrote); `_lead_marks()` (R8–R10's
  precedence, git reads at `<branch>:<folder>/runs/`); `_lead_line()`, which never raises and
  returns the line or the coverage word (R11); and `measure_change()`'s `finish()` appending it
  after every other line.
  A dropped change is told by its intent's `stage: dropped` on the branch, so `measure_change`'s
  signature stays `(main, branch, cfg)` (a test wraps it with exactly those three).
- `plugins/factory/scripts/factory.py`: `record_cost()` takes `started`/`ended` keywords, which
  `cmd_agent()` takes with `_utc_now()` around `_claude()`; `_record_land()`'s row gains `since`.
- `scripts/retro.py`: `process_views()` gains `out["lead"]`, computed before the
  `if not measured` exit; `render_report()` adds the lead table and sentence to `cycle`.
- Tests: `tests/test_metrics.py` (R4–R6), `tests/test_sdlc.py` (R1–R2), `tests/test_archive.py`
  (R1 under GitHub numbering, R7, R8, R10–R12, the pin of R9's rows against closing's readers),
  `tests/test_factory.py` (R9; the exact-row assertion in the costs test gains the two keys),
  `tests/test_land.py` (R9: the land-times row's `since`), `tests/fixtures/land-record-cases.json`
  (a row with `since`, so the board/factory pin covers it), `tests/test_retro.py` (R13–R15),
  `tests/test_adoption.py` (a real `new`→`close` carries `Sdlc-Lead … source=git`).
- Docs: `docs/REFERENCE.md` *Metrics* and *Retrospectives*, `docs/RETRO-SCORECARD.md` S1 (R16).

Reused, not re-derived: `frontmatter_list()` for `opened:`, `_minutes()`/`_pairs()` for the
trailer, `parse_trailers()` as is, `_agent_sessions()` for the factory fallback's roles,
`_utc_now()` and its format in the factory.

## Work order

1. **Pure arithmetic** (R4–R6): `metrics.lead_time()`, `lead_trailer()`, the round trip through
   `parse_trailers()`. Tests first in `test_metrics.py`.
2. **Recording the start** (R1–R3): `_with_opened()` in `cmd_new()`; tests that a change under
   local and GitHub numbering has a parsable `opened:`, `id: 012` stays, ship/upgrade keep it.
3. **The factory's times** (R9): `record_cost(started=, ended=)`, `_record_land()`'s `since`;
   tests on the rows and that the board's and `run_cost()`'s figures don't move.
4. **Close records it** (R7, R8, R10–R12): `opened_at()`, `_lead_marks()`, `finish()`'s line;
   tests on fixture branches: runs, hand-built with and without transcripts, no `opened:`, a bad
   one, a raising reader, a drop.
5. **Retro reads it** (R13–R15): `process.lead` and the report's lead block.
6. **Docs** (R16).

Each step leaves the tree working: 1 adds unused functions, 2 adds a line nothing reads yet, 3
adds keys nothing reads yet, 4 reads 1–3, 5 reads 4.

## Tests

- R1: `test_new_writes_opened_to_the_minute_under_either_numbering` (sdlc), with `id: 012`.
- R2: `test_shipping_and_upgrading_keep_opened` (sdlc).
- R3: no new test: `test_defaults.py` and the drift gate stay green, unedited.
- R4: `test_lead_time_parts_sum_to_lead`, `test_overlapping_agents_count_once` (metrics).
- R5: `test_lead_time_leaves_out_what_it_cant_know` (parametrized over each case).
- R6: `test_lead_trailer_round_trips` (metrics), docstring names the line.
- R7, R8: `test_close_records_lead_time_from_the_runs` (archive): a factory fixture with
  committed `costs.jsonl` (`started`/`ended`, overlapping reviewers, two approver rows) and
  `land-times.jsonl` (`since`); `_lead_marks()`'s marks exact, the `Close` commit's line
  `source=runs`, every other trailer unchanged.
- R9: `test_each_agent_run_records_its_figures…` updated with `started`/`ended`; a land-times row
  carries `since`; `test_the_runs_rows_are_read_by_close_as_written` pins closing's reader to rows
  `record_cost()` and `_record_land()` wrote.
- R10: hand-built with transcripts (`source=transcripts`, split present), without
  (`source=git`, only `lead` and `ready_wait`), factory with old rows and sessions
  (`source=transcripts`).
- R11: no `opened:` → `lead=none`; bad → `lead=bad-opened`; raising → `lead=failed`; close lands.
- R12: a dropped change's `Drop` commit has no `Sdlc-Lead`.
- R13, R14: `test_lead_time_by_tier_and_way` (p85 of 10..100 is 90; unmeasured counted, never
  moves a median), and the existing process test unchanged on records without the line.
- R15: `render_report()` shows the lead table and shares.
- R16: no test; ship shows the docs edit (`sdlc.py context`).

## Built differently from the spec

- A first mark before `opened` (the session that ran `new` began before it) is clipped to
  `opened`, rather than dropping the split as out of order (`lead_time()`'s docstring).
- A factory change with neither timed rows nor factory sessions records `lead` and `landing`
  only: nothing in git says when its approver finished, so `ready_wait` is unknown (a decision in
  the round's report).
- `opened` after the close gives no line, and the coverage says `lead=bad-opened`.

## Rollback

`git revert` undoes all of it. What it doesn't: every `Close` commit made while this was in
carries an `Sdlc-Lead` line, and every `intent.md` made by `new` an `opened:` line. Both are
additive and inert once reverted (`parse_trailers()` keeps an unknown line as a dict nobody reads;
YAML reads `opened:` as a string), so nothing needs undoing. The factory's run rows keep
`started`/`ended`/`since`, which every reader ignores.
