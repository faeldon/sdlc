---
id: 162
slug: lead-time
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 162 — Lead time, and where it goes, on every change · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code before designing:

- `created:` is read as a date by `load_change()`, `_age_days()`, `measure_change()` and the drop
  record's `days_open` (`date.fromisoformat`). Adding a time to it would break each of them, and
  every host's history already holds it as a date.
- `runs/costs.jsonl` rows (`factory.py record_cost()`) hold `duration_ms` but no time of day.
  `runs/land-times.jsonl` rows (`_record_land()`) hold `seconds` but no time either. So today no
  committed run file can say when an agent started or when a landing began.
- A factory change's branch tip is rebased by `land --close`, which rewrites its committer date
  but keeps its author date.
- `parse_trailers()` already reads an unnamed `Sdlc-<Key>: k=v …` line as `out[key] = fields`,
  so a new `Sdlc-Lead` line needs no parser change. Retro gets each change's trailers as
  `rec["metrics"]` (`sdlc.py`, closed-change records).
- The retro report's `{{cycle}}` value is built in `retro.py`. Lead time can go there without
  editing `templates/retro.md`, which is `[review] irreversible`.

The intent's outcome of recomputing 139–157 against the hand-run analysis is dropped, by the
person's call: the unit tests below prove the arithmetic and each source on fixtures.

1. R1. `sdlc.py new` writes `opened: YYYY-MM-DDTHH:MMZ` (UTC, to the minute) into the new
   `intent.md`, on the line after `created:` (before the closing `---` when a host's template has
   no `created:`). It does this under GitHub numbering and local numbering alike. Every other byte
   of the rendered template is kept. Tests (`tests/test_sdlc.py`): fail if a change made by `new`
   under either numbering lacks a parsable `opened:`, or if `id: 012` stops being `012`.
2. R2. `opened:` is read as text (`frontmatter_list()`), never through YAML. `stamp_shipped`,
   `_stamp` and `upgrade` leave it as it is. A test fails if shipping or upgrading a change
   changes its `opened:` line.
3. R3. `templates/` and `defaults/` are not edited, and `TEMPLATE_READS` doesn't gain `opened`:
   `new` writes the line, so a host's own `intent.md` template needs nothing. `sdlc.py drift`
   stays clean. `test_defaults.py` and the drift gate pass unchanged.
4. R4. `metrics.py` gains a pure `lead_time(opened, closed, first, ready, landing, intervals)`.
   It takes aware datetimes (any of `first`, `ready` or `landing` may be None) and a list of
   `(start, end)` agent intervals, and returns seconds for `lead` and, when known, `queued`
   (opened→first), `agents` (the union of the intervals clipped to first→ready, so reviewers run
   together count once), `idle` (first→ready less `agents`), `ready_wait` (ready→landing, or
   ready→closed when `landing` is None) and `landing` (landing→closed). It has no subprocess and
   no import of `sdlc.py` (`tests/test_modules.py`). A test fails if the parts present don't sum
   to `lead` to the second, or if two overlapping intervals are counted twice.
5. R5. A part `lead_time()` can't know is left out, never 0. With no `first` or no `ready`,
   `queued`, `agents` and `idle` are absent. With `ready` before `first`, or any time after
   `closed`, the split is absent and `lead` alone is kept. With `opened` after `closed`, nothing
   is returned. Tests: one for each case, failing if a missing part shows as `0`.
6. R6. `metrics.lead_trailer(lead, source)` writes one line: `Sdlc-Lead: lead=<m> [queued=<m>
   agents=<m> idle=<m>] ready_wait=<m> [landing=<m>] source=<runs|transcripts|git>`. It holds
   whole minutes and a source word only: no path, session id or name. `parse_trailers()` reads it
   back as `metrics["lead"]` with integer values. A round-trip test fails otherwise, and the
   module docstring's contract lists the line.
7. R7. Close's `measure` step (`measure_change()` in `closing.py`) adds `Sdlc-Lead` to a landing
   change's trailers, after the existing lines, which stay as they are. `closed` is the moment
   measure runs (the `Close` commit follows within the same close), `opened` comes from the
   intent on the change's branch, and the rest comes from R8–R10. A test in `tests/test_metrics.py`
   or the close tests fails if a `Close` commit for a change with `opened:` lacks the line, or if
   any existing trailer line changes.
8. R8. Factory change (`decision.md` on the branch):
   - `first` is the earliest `started` among `runs/costs.jsonl` rows.
   - `intervals` are each row's `[started, ended]`.
   - `ready` is the `ended` of the last `approver` row that started before `landing`.
   - `landing` is the earliest `since` among `runs/land-times.jsonl` rows. With no such row, it
     is the branch tip's author date (`%aI`).

   Everything is read from git at `<branch>:<folder>/runs/`, so a close on another machine still
   records it: `source=runs`. Tests fail if a fixture branch's committed run files give any other
   figures, or if reviewer rows that overlap count more than once.
9. R9. `factory.py` records the times R8 reads, extending its run files without redefining them:
   - `record_cost()` rows gain `started` and `ended` (`%Y-%m-%dT%H:%M:%SZ`), taken around the
     `claude` call in `agent`.
   - `_record_land()`'s rows gain `since`, the step's `SINCE:`.
   - `read_land_times()`, the board's copy and `run_cost()` ignore the new keys, and their
     figures don't change.

   Tests (`tests/test_factory.py`, `tests/test_board.py`) fail if a row lacks the keys or if any
   board or cost figure moves. A test pins closing's reader against a row `record_cost()` wrote.
10. R10. Changes R8 can't measure from run files:
    - **Built by hand** (no `decision.md`): `ready` is the branch tip's author date, the commit
      ship made after its review and the person's yes. `landing` is None, since close is its
      landing, so its wait is `ready_wait`. `first` and `intervals` come from the transcripts
      when `measure_change()` already read them: the change's first event, and each `turn` as
      `(ts - ms, ts)` with its sub-agent runs. That gives `source=transcripts`.
    - **Factory change whose rows predate R9's keys:** the factory sessions' `subagent` events
      (roles from `runs/*.sessions`) stand in for the rows. Also `source=transcripts`.
    - **No transcripts:** `lead`, `ready_wait` and (for a factory change) `landing` alone, with
      `source=git`.

    Tests fail if a hand-built change without transcripts records `queued`, `agents` or `idle`, or
    records none of `lead` and `ready_wait`.
11. R11. Measuring never refuses.
    - A change with no `opened:` (closed before this, or a hand-written intent) gets no `Sdlc-Lead`
      and `Sdlc-Coverage` gains ` lead=none`.
    - An unparsable `opened:` gets ` lead=bad-opened`.
    - An exception while timing gets ` lead=failed`.
    - In every case the other trailers are still written, and close still lands.

    A test fails if any of these raises or drops another trailer.
12. R12. A dropped change's `Drop` commit carries no `Sdlc-Lead`: it never landed. A test fails
    if `_drop_record()`'s trailers hold one.
13. R13. `sdlc.py retro`'s `process` gains `lead`:
    - For each tier and way of building (`Sdlc-Mode`, `manual` or `factory`): `n`, the `median`
      and the 85th percentile (`p85`, nearest rank: the sorted value at `ceil(0.85·n) − 1`) of
      `lead`.
    - `shares`: for each part, its sum over the changes that recorded it, divided by the sum of
      their `lead`, to two places, with how many changes each share covers.
    - `measured` and `unmeasured`: changes with and without `Sdlc-Lead`.

    Tests (`tests/test_retro.py`) fail if a change without the line moves a median, if it isn't
    counted in `unmeasured`, or if p85 of `[10, 20, …, 100]` isn't 90.
14. R14. `elapsed` and every existing `process` figure and table are unchanged. Retro computes
    `lead` whether or not any change has `elapsed`. A test fails if the existing `cycle`, `time`
    or `capacity` output differs on a window with no `Sdlc-Lead`.
15. R15. The report's *Cycle time* section (its `{{cycle}}` value) shows a lead-time table
    (Tier, Way, Changes, Median lead, 85th percentile) and a sentence giving the shares and the
    unmeasured count, under the existing table, or alone when nothing has `elapsed`. A
    `retro_report()` test fails without it.
16. R16. `docs/REFERENCE.md`'s *Metrics* section describes `opened:`, `Sdlc-Lead`, its parts,
    sources and absences, and that lead time starts at `new`, even for a change opened from an
    issue someone filed. Its *Retrospectives* section describes the lead-time figures.
    `docs/RETRO-SCORECARD.md`'s S1 rows say what is now recorded. `sdlc.py context` lists them,
    and ship shows the edits.

## Design

**Recording the start.** In `cmd_new()`, after `render_template()` fills `intent.md`, a small
helper `_with_opened(text, stamp)` inserts `opened: <stamp>` after the frontmatter's `created:`
line, or before its closing `---`. It edits lines in place, as `stamp_shipped` does. The stamp is
`datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")`. To the minute is what the intent asks. The
format has no seconds, so a YAML reader that sees it reads a string, never a timestamp. The line is
written by `new`, not the template, so every host gets it on update with no `setup` rerun and no
drift. A reader, `opened_at(text) -> datetime | None`, parses only that format, so a hand-edited
value that doesn't fit reads as None, and R11 reports it. A change opened from an issue someone
filed (intake, `closes:`) starts at `new` too. The time from the filing is a different,
customer-facing figure, outside this intent.

**The pure part.** `metrics.lead_time()` works in seconds on aware datetimes:
- `agents` merges the sorted intervals, clips them to `[first, ready]` and sums them.
- `idle = (ready − first) − agents`.
- `ready_wait` runs to `landing`, or to `closed` when `landing` is None.
- `landing = closed − landing`.

The parts present always sum to `lead`. `lead_trailer()` rounds each to minutes by `_minutes()`,
so the written parts may miss `lead` by a minute or two. That is fine, because retro sums from
the trailers and its shares are ratios. Both live beside `trailers()` and are added to the
docstring's contract as extensions:

    lead_time(opened, closed, first, ready, landing, intervals) -> dict
    lead_trailer(lead, source) -> line

**Gathering at close.** `measure_change()` already reads the intent, the tip's trailers, the
runs' sessions and models from git, and the transcripts when allowed. A new
`_lead_marks(main, branch, folder, way, events, roles)` in `closing.py` returns
`(first, ready, landing, intervals, source)` by R8–R10's precedence. It reads committed run files
first, then factory `subagent` events, then hand turns, then git alone. `measure_change()` calls
`lead_time()` and appends `lead_trailer()` after `finish()`'s lines, in its own `try`, so a
failure costs only that line (R11). `cmd_close`'s `measure()` tells it whether the change lands or
is dropped, and only a landing is timed (R12). `closed` is `datetime.now(UTC)` at measure, as
`from_history()` already uses. The `Close` commit is made moments later in the same run, and a
rerun re-measures.

**Recording the factory's times.** `cmd_agent` takes `_utc_now()` before and after `_claude()`
and passes both into `record_cost()`'s row. `_record_land()` writes the replaced step's `since`
into its `land-times.jsonl` row. Both run files are committed with the change when landing ships
it, which is where close reads them. The plan confirms the first landing rows are written before
`land`'s ship commit, and R8 falls back to the tip's author date where they aren't.

**Reading it back.** In `retro.py`'s `process_views()`, `lead` is computed from
`(c["metrics"] or {}).get("lead")` before the `if not measured: return out` early exit, grouped by
`str(tier)` and `metrics["mode"]`. `retro_report()` adds the lead block to `values["cycle"]`. The
JSON gains `process.lead`, and every other key is unchanged. `_lean()`'s rule still holds: summaries
are built from the full records, and a change's own `Sdlc-Lead` is printed only with `--metrics`.

**Edge cases.**
- A change closed before this has no `opened:`, so it gets no line and retro counts it as
  `unmeasured`.
- A change opened before this lands and closed after it has no `opened:` either, so it is
  unmeasured too.
- A factory run in flight when this lands has rows without times, so R10's transcript fallback
  applies.
- A restarted factory run has several approver rows: `ready` is the last one before landing.
- A clock that runs backwards leaves `lead` alone (R5).

## Contracts touched

- **The metrics trailer format is extended, never redefined** (`metrics.py` docstring, AGENTS.md
  *Metrics*). `Sdlc-Lead` is a new line after the existing ones. `Sdlc-Coverage` gains a `lead=`
  word only when the line is missing. Every existing line is untouched (R7).
- **Measuring never refuses.** Lead time has its own `try`, and absence is said in coverage (R11).
- **`metrics.py` stays pure.** `lead_time()` and `lead_trailer()` take values. All git reads are in
  `closing.py` (R4, `tests/test_modules.py`).
- **Frontmatter read as text; `stamp_shipped` edits in place.** `opened:` is inserted and read as
  a line, never round-tripped through `frontmatter.dumps()` (R1, R2).
- **One shape for the shipped docs; `irreversible = ["defaults/", "templates/"]`.** Neither is
  edited, so there is no `record` or drift work and nothing a revert can't reach (R3). Putting the
  report's lead block inside `{{cycle}}` is what avoids a `templates/retro.md` edit.
- **`TEMPLATE_READS`.** It is not extended: the plugin never requires `opened:` from a template.
  `breaking` is not touched.
- **`closing.py` is `[review] sensitive`.** The edit is inside `measure_change()` and a new helper.
  No git step of close changes, and no path to losing work is near it. The review runs at full
  depth anyway.
- **`factory.py` never imports `sdlc.py`; `sdlc` reads factory files with copies of the parsing,
  pinned.** Closing's reader for the new `started`, `ended` and `since` keys is pinned by a test
  against rows the factory's own writers produce (R9).
- **Windows.** Times are formatted with `strftime` in UTC, not the locale. No new subprocess and
  no new file writes in `sdlc.py`. `intent.md` is still written with `newline="\n"`.
- **Nothing local / nothing public names the agent.** The trailer holds minutes and a source word
  only.
- **Must land before R6** (splitting `cmd_close` into steps). This touches only `measure()`'s
  inner call, so R6 moves it unchanged.

No invariant needs to change.

## Alternatives rejected

- **A time added to `created:`.** At least six readers parse it as a date, and hosts' history
  holds dates. Every reader and every old folder would need a dual-format rule. A new line is
  additive.
- **Retro computing lead time from history (`Close^`'s intent and run files) instead of a
  trailer.** That breaks the rule that a change's numbers live on its `Close` commit. It would make
  retro read the change folder's files, and it would lose the transcript fallback, which exists
  only at close.
- **The issue's open time as the start.** Local numbering has no issue (seed 2026-11-18-106), and
  the core never calls `gh`. `new`'s own time is the same moment for an issue `new` opened. For an
  issue someone filed earlier, the wait before `new` is a different figure, outside this intent.
- **The start of `/sdlc:ship` as a hand-built change's ready time.** Only transcripts know it, so
  it would be missing whenever they are. Ship's commit is in git on every machine.
- **Splitting the hand-built time by transcripts only, or not at all.** The split is recorded
  when transcripts exist and left out otherwise, so the line always exists and never invents an
  `agents=0`.
- **Agent time from `duration_ms` sums.** Reviewers run in parallel, so a sum double-counts. Only
  intervals can be merged, and only start and end times give them.
- **A new run file of marks (`runs/marks.jsonl`).** That is a new file for the board, the landing
  and close to keep in step. Two keys on rows that already exist cover it.
- **A new `{{lead}}` placeholder in `templates/retro.md`.** It is an irreversible path, and a
  host's own copy wouldn't show it until setup reran.
- **Recomputing 139–157 against the hand-run analysis.** It would need a one-off script and the
  hand figures, and it would prove only what R4–R10's fixture tests already pin. Dropped by the
  person's call.

## Verification

- `./check.sh`: ruff, the format check, `pytest -n auto` and `claude plugin validate --strict`,
  all green. Healthy is no failures, no reformat, and `validate` passing.
- `uv run --group dev pytest -q tests/test_metrics.py tests/test_retro.py tests/test_sdlc.py
  tests/test_factory.py tests/test_board.py tests/test_modules.py -n auto`: the new R1–R15 tests
  pass beside the existing ones, and no existing board, cost or retro figure changes.
- `uv run --group dev pytest -q -m portable`: green. The Windows job runs the `opened:` and
  `lead_time()` tests.
- `uv run --quiet --script scripts/sdlc.py drift`: reports nothing (R3).
- `uv run --quiet --script scripts/sdlc.py retro`: `process.lead` is present, with every change
  in the window counted in `unmeasured`, since none was closed with `opened:`. `process.cycle` is
  unchanged.
- `tests/test_adoption.py` still runs a change from `new` to `close` in a bare repo, and its
  `Close` commit carries an `Sdlc-Lead` line with `source=git`.

