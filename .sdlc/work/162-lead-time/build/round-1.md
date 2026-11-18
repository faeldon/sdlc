# Build report: 162-lead-time, round 1

All of R1–R16 is built. Every test I ran passes, after one fix: the full gate run (`factory.py check 162`) failed on a single test, which I fixed. I didn't rerun the whole gate afterwards; I reran the failing test and every file this change touches, and they pass. Nothing is committed.

## Slices built

1. **The arithmetic (R4–R6).** `metrics.py` gets `lead_time()` and `lead_trailer()`, and its docstring now lists both and the `Sdlc-Lead` line. Agent intervals are merged and clipped to the span from first to ready, so reviewers running in parallel count once. A part that can't be known is left out rather than written as 0. `parse_trailers()` reads the new line without any change.
2. **When a change was opened (R1–R3).** `cmd_new()` writes `opened: YYYY-MM-DDTHH:MMZ` (UTC) on the line after `created:`, or before the closing `---` if there is no `created:`. It goes through `_with_opened()`, which edits lines in place. No template or default is edited.
3. **The factory's times (R9).** `cmd_agent` records `started` and `ended` around the `claude` call, and `record_cost()` writes them into the cost row. `_record_land()`'s rows gain `since`. Every existing reader ignores the new keys.
4. **Close records it (R7, R8, R10–R12).** In `closing.py`:
   - `opened_at()` reads the `opened:` line.
   - `_timed_rows()` and `_land_sinces()` read the factory's run files.
   - `_lead_marks()` picks the source in order: the run files, then transcripts, then git.
   - `_lead_line()` never raises. It returns the line, or a word for `Sdlc-Coverage`: `lead=none`, `lead=bad-opened` or `lead=failed`.
   - `finish()` adds the line after all the existing ones. A dropped change (one whose intent says `stage: dropped`) gets no line. I kept `measure_change`'s signature as it was, because a test wraps it with exactly three arguments.
5. **Retro reads it (R13–R15).** `process_views()` gains `process.lead`, with count, median and 85th percentile (nearest rank) per tier and way of building, each part's share, and measured/unmeasured counts. It is computed before the early exit, so it works even when no change has `elapsed`. `render_report()` puts the lead table and the shares inside the *Cycle time* section, so `templates/retro.md` isn't touched.
6. **Docs (R16).** `docs/REFERENCE.md` describes the new line and figures in *Metrics* and *Retrospectives*. In `docs/RETRO-SCORECARD.md`, the lead-time headline and the flow-efficiency/ready-wait rows are marked captured, and predictability is marked partly captured.

## Tests added and what they prove

- **`test_metrics.py`**:
  - The parts add up to the lead time, and overlapping reviewers count once (R4).
  - Each case that can't be measured leaves the part out rather than writing 0, and an `opened` after the close gives nothing (R5).
  - A first event before `opened` is clipped to `opened`.
  - The trailer reads back with whole minutes and a source word (R6).
- **`test_sdlc.py`**:
  - `opened:` is written to the minute under local numbering for both tiers, `id: 012` stays as written, and every other line of the template is unchanged (R1).
  - `opened:` goes before the closing `---` when there's no `created:`.
  - Shipping, dropping and upgrading leave `opened:` alone (R2). This one passed before the change: it guards behaviour that must not change.
- **`test_archive.py`**:
  - `opened:` is written under GitHub numbering too (R1).
  - The marks taken from a factory change's run files are exact, and the `Close` commit carries `source=runs` with every other trailer byte-identical (R7, R8).
  - A factory change with no landing row is timed from its tip's author date.
  - A change built by hand without transcripts records only `lead` and `ready_wait` with `source=git`; with transcripts it gets the full split (R10).
  - A factory change from before the times were recorded falls back to its sessions (R10).
  - No `opened:`, a bad one, and a reader that raises each still let close land, with the right coverage word (R11).
  - A dropped change gets no line (R12).
  - Closing's readers are pinned to rows the factory itself writes (R9).
- **`test_factory.py` and `test_land.py`**: the cost rows carry `started`/`ended`, and the land-times rows carry `since` (R9).
- **`land-record-cases.json`**: a row with `since` added, so the existing test that the board and the factory read land-times rows the same way covers it.
- **`test_retro.py`**: p85 of 10…100 is 90, an unmeasured change is counted apart and moves no median, and shares are only for the changes that recorded each part (R13). Every existing view is unchanged when the window has no lead lines (R14). The report shows the lead table under the elapsed table, or alone (R15).
- **`test_adoption.py`**: a real `new`→`close` run through `uv run --script` puts `Sdlc-Lead … source=git` on the `Close` commit.

## Named runs

- The full gate in a gate slot: 2988 passed, 28 skipped, 1 failed. The failure was `test_registry.py`, because `_with_opened` sat between `cmd_new` and `cli_new`. I moved it (and `OPENED_FORMAT`) above `cmd_new`, and `test_registry.py` then passed 16 of 16.
- The touched files rerun after that fix: 804 passed.
- `ruff check .` and `ruff format --check .` are clean.

## plan.md

I wrote it before any code, and then updated it where the build departed from it:
- the new helpers (`_lead_line`, `_timed_rows`, `_land_sinces`, `RUN_TIME_FORMAT`);
- where `_with_opened` sits (above `cmd_new`, for the registry test);
- the extra test files (`test_land.py`, the fixture, `test_adoption.py`);
- a new section, "Built differently from the spec", listing three departures.

## notes.md

Nothing left there.

## Decisions

- DECISION: [default] A factory change with neither timed run rows nor factory sessions records `lead` and `landing` only, with no `ready_wait`. Going ahead with that unless told otherwise.
  - OPTION: leave `ready_wait` out — nothing in git says when the approver finished, because the factory commits the change once, at landing; but the line is shorter than R10's wording
  - OPTION: use the tip's author date as ready — the line always has a `ready_wait`; but it would be about 0 and wrong, since the tip is written at landing
  - WHY: R5 says a part that can't be known is left out, never invented
- DECISION: [default] When the first agent run or edit comes before `opened`, it is clipped to `opened` and the split is kept. Going ahead unless told otherwise.
  - OPTION: clip to `opened` — a hand-built change whose `/sdlc:intent` session ran `new` still gets its split, with `queued` at 0; but the minutes before `new` aren't counted anywhere
  - OPTION: treat it as out of order and keep `lead` alone — strict; but almost every hand-built change with transcripts would lose its split
  - WHY: the spec says lead time starts at `new`, so time before it is outside lead time by definition
- DECISION: [default] When `opened` is after the close, there is no line and the coverage says `lead=bad-opened`. Going ahead unless told otherwise.
  - OPTION: `lead=bad-opened` — reuses a word the spec already defines; but it lumps a clock fault in with a malformed value
  - OPTION: a new word such as `lead=clock` — more precise; but it's one more word for retro to know
  - WHY: R5 returns nothing in this case, and R11 has no word of its own for it

## Evidence

$ uv run --group dev pytest -q tests/test_metrics.py -k "lead or agents_before"
10 failed, 178 deselected in 0.36s
exit: 1

$ uv run --group dev pytest -q tests/test_metrics.py -k "lead or agents_before"
10 passed, 178 deselected in 0.12s
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py -k "opened"
3 failed, 2 passed, 264 deselected in 23.33s
exit: 1

$ uv run --group dev pytest -q tests/test_sdlc.py -k "opened"
5 passed, 264 deselected in 1.40s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py::test_each_agent_run_records_its_figures_and_a_resume_is_not_counted_twice tests/test_land.py::test_each_landing_step_change_writes_a_times_row
2 failed in 1.94s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py::test_each_agent_run_records_its_figures_and_a_resume_is_not_counted_twice tests/test_land.py::test_each_landing_step_change_writes_a_times_row tests/test_board.py -k "cost or land_times or pinned or run_seconds or record"
17 passed, 285 deselected in 5.13s
exit: 0

$ uv run --group dev pytest -q -n 8 tests/test_archive.py -k "lead or opened or run_rows"
5 failed, 1 passed in 25.94s
exit: 1

$ uv run --group dev pytest -q -n 8 tests/test_archive.py tests/test_metrics.py tests/test_train.py tests/test_nits.py tests/test_modules.py tests/test_adoption.py
430 passed in 88.93s (0:01:28)
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k "lead"
3 failed, 142 deselected in 0.16s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py
145 passed in 43.07s
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
291 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 162
FAILED tests/test_registry.py::test_each_command_sits_beside_its_handler[sdlc]
1 failed, 2988 passed, 28 skipped in 120.04s (0:02:00)
exit: 1

$ uv run --group dev pytest -q tests/test_registry.py
16 passed in 0.96s
exit: 0

$ uv run --group dev pytest -q -n 8 tests/test_metrics.py tests/test_sdlc.py tests/test_archive.py tests/test_retro.py tests/test_factory.py::test_each_agent_run_records_its_figures_and_a_resume_is_not_counted_twice tests/test_land.py::test_each_landing_step_change_writes_a_times_row tests/test_board.py::test_the_land_record_readers_are_pinned_copies tests/test_adoption.py tests/test_registry.py tests/test_modules.py
804 passed in 38.04s
exit: 0
