I built all six slices. Every named test passes, and the full gate passed (ruff, format, 3183 tests with 29 skipped, plugin validate). Nothing is committed.

**Slices built**
1. **Reading rows from text and back** (`scripts/indicators.py`). `host_rows()` checks an indicator's output against the row shape (R1) or says why it isn't rows (R2). `report_rows()` reads a past report's indicator table back by its exact header (R4). Small helpers write the table cells, values and signed changes, and the reader undoes the same escaping. The module still uses only `json` and `math`.
2. **Rows in `retro`'s JSON** (`scripts/retro.py`). `_architecture()`'s `host` now goes through `_indicator_rows()`. A failure, a timeout or cut output is never read as rows; each says why in `not_rows` and keeps its fields as before. When the output is rows, `output` becomes null (R3). Each row's `last` comes from the last retrospective's committed report, read with `git show`, and `change` is the value minus `last` (R4).
3. **The report.** The template gets `## Indicators` / `{{indicators}}` after `## Spend`. `_indicators_text()` shows each command's table, or one sentence when there is no table, or says no indicators are set (R5, R6). `retro_report()` now runs `retro.indicators`, and no other host command (R7). `TEMPLATE_READS` names the new section (R9), and `.sdlc/setup.json` is re-recorded.
4. **`.sdlc/function-heat.py`** now prints two JSON rows per function, one for commits and one for lines (R10). This repo's real output is 120 rows, 9,853 characters, well under the 20,000-character limit, and parses with no reason given.
5. **Setup** gets an **Indicators** item in `drafts.md` Step 2 and a `[retro] indicators` line in Step 3's config draft. `READS_CONFIG["sdlc:setup"]` now includes `retro.indicators` (R11).
6. **Docs** (R12): REFERENCE.md's *Retrospectives* (the row shape, the pass-through, the table) and *After an update*, its config example line, retro's `SKILL.md` `host` bullet, and AGENTS.md.

**Tests added and what they prove**
- `test_indicators.py`:
  - `test_indicator_rows_are_read_from_json_lines` (R1)
  - `test_output_that_isnt_rows_passes_through_with_its_reason`, 17 cases (R2)
  - `test_the_last_report_s_rows_are_read_back_by_their_header` (R4: only the exact header is read; a row shown twice gives null)
  - `test_a_cell_escapes_what_a_table_would_split_on`
- `test_retro.py`:
  - `test_indicator_rows_reach_the_architecture_block` (R3)
  - `test_a_failed_or_cut_indicator_passes_through_with_its_reason` (R2: plain text, exit, truncation, timeout)
  - `test_an_indicator_is_compared_with_the_last_retrospectives_report` (R4: an older retrospective and an edited report in the tree are ignored; a retrospective with no report gives null)
  - `test_the_report_renders_indicator_rows_as_a_table` (R5: no raw output or stderr reaches the report)
  - `test_the_report_says_no_indicators_set` (R6)
  - `test_indicator_rows_round_trip_through_the_report` (R8)
  - `test_retro_and_its_report_show_the_same_figures` now has the split R7 assertion. `retro` itself runs `retro.evidence` only with a product doc, so the "it ran" check covers just the indicator and test-times commands.
  - `test_the_report_renders_spend` is extended for R9.
- `test_function_heat.py`:
  - `test_each_function_is_two_indicator_rows`
  - `test_this_repos_rows_stay_under_the_evidence_limit`, which uses the longest names in the four files at 7-digit figures
  - the subprocess test, which now parses each line as JSON (R10)

**Changes to `plan.md`:** I wrote it before the code, and the build follows it. One difference from the spec's design: `_indicator_rows()` takes `since` from its caller rather than looking up the last retrospective again.

**Left in `notes.md`:**
- A unit that is literally `—`, or a name or unit with spaces at either end, reads back from the report as a different key, so it gets no `last`. The spec doesn't forbid either.
- `sdlc.py retro` run from a worktree runs the main checkout's `function-heat.py`. So the spec's `retro` verification line will only show rows after this lands.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_indicators.py
66 passed in 0.05s
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k "indicator or same_figures or renders_spend"
9 passed, 175 deselected in 106.44s (0:01:46)
exit: 0

$ uv run --group dev pytest -q tests/test_function_heat.py
8 passed in 0.49s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py
416 passed in 0.62s
exit: 0

$ uv run --group dev pytest -q tests/test_indicators.py tests/test_function_heat.py "tests/test_skills.py::test_skills_read_host_specifics_from_config"
94 passed in 75.00s (0:01:15)
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_retro.py tests/test_defaults.py tests/test_indicators.py tests/test_windows.py tests/test_modules.py
440 passed in 27.44s
exit: 0

$ uv run --quiet --script scripts/sdlc.py record
  wrote  .sdlc/setup.json  (plugin 1.10.0, 3 doc(s))
exit: 0

$ uv run --quiet --script .sdlc/function-heat.py | wc -c
    9853
exit: 0

$ uv run --group dev python -c '…indicators.host_rows(open("/tmp/heat177.jsonl").read())…'
None 120
exit: 0

$ uv run --group dev ruff check . && uv run --group dev ruff format --check .
All checks passed!
308 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 177
All checks passed!
3183 passed, 29 skipped in 502.46s (0:08:22)
✔ Validation passed
✔ Validation passed
exit: 0
