I built R1–R10 of 118; R11 (filing the suite-pruning seed) is ship's job. The gate passes with 2,200 tests (9 skipped), and nothing is committed (HEAD is still `971980f`).

## Slices built

1. **Words (R1).** Each `human` event now carries `words`: a slash command's name plus its arguments, or the words of a typed reply with the harness's tagged blocks taken out. An interrupt counts 0. Words are summed per stage and written as `words=` on `Sdlc-Stage` and `Sdlc-Totals`. Only the count is kept, never the text.
2. **Tool calls (R2, R3).** There is now a `tool{name, error, role?}` event for every `tool_use`, in the session itself and in `_run()` (sub-agents and factory agent sessions, tagged with their role). The name comes from `_prompt_name()`. `error` is the result's `is_error`, and stays `None` when a call got no result. `summarize()` keeps calls, errors and a per-stage count for each name. Each name gets an `Sdlc-Tool: <name> calls= errors= <stage>=…` line, `tools=` goes on `Sdlc-Totals`, and `parse_trailers()` reads them back into `tools`. Close's `measure` needed no change.
3. **Comment counting (R4).** `indicators.comment_lines()` uses the `COMMENT_MARKERS` table from the spec. Prose files are never counted, and an unknown suffix goes to `unknown_lines`.
4. **The spend summary (R6, R7).** `indicators.spend()` gives each tier's median for three measures: comment share, `out` tokens per code line and tool calls per code line. A tier with fewer than 3 changes gets no median. It names any change more than twice its tier's median, with by how much, and lists the 10 most-called tools and the 10 with the most errors.
5. **Retro's `spend` block (R5, R8).** `_added_diff()` and `_spend()` in `retro.py` build it, and `retro()["spend"]` returns it. Each unrecorded change says why: "not measured at close", the coverage reason, or "closed before tool calls and words were counted". `cmd_retro()` prints `spend.changes` only with `--metrics`.
6. **The report (R9).** `templates/retro.md` has a `## Spend` section with `{{spend}}`, filled by `render_report()` and `retro_report()`. `TEMPLATE_READS["retro.md"]` now names that heading and placeholder, so a host's older override shows up in drift's `breaking` list. `skills/retro/SKILL.md` describes `spend` in Step 0 and how to weigh it in the Process pass.
7. **Docs (R10).** `docs/REFERENCE.md` gains `words=`, `Sdlc-Tool` and `tools=` under *Metrics*, and the `spend` block plus the override note under *Retrospectives*.

On this repo's own history, `sdlc.py retro` now reports `spend` with all 43 changes unrecorded (as expected before this one closes), comment medians for both tiers and 10 outliers. `sdlc.py drift` is clean.

## Tests added

- **test_metrics:**
  - `test_words_are_counted_and_no_text_leaves` (R1)
  - `test_every_tool_call_is_counted_with_its_error` (R2: names, `is_error`, a call with no result, a factory role's calls, no paths in events)
  - `test_tool_lines_round_trip` (R3)
  - `test_a_close_from_before_tool_lines_is_unrecorded` (R3, R8). This one passed before any code; it pins behaviour that already held.
  - I widened `test_no_text_leaves_a_human_event` so it accepts the integer `words` count.
- **test_indicators:**
  - `test_comment_lines_by_suffix` (R4: a `#` line inside a string counts by design, prose is skipped, unknown suffixes are kept apart, an added `++` line past the header is handled)
  - `test_spend_names_a_change_twice_its_tier_median` (R6: a change at exactly 2× is not named)
  - `test_a_tier_with_two_changes_names_no_outlier` (R6, R8)
  - `test_spend_ranks_the_tools` (R7)
- **test_retro** (git fixtures):
  - `test_spend_lists_each_change_and_says_what_is_unrecorded` (R5, R8, the `--metrics` strip)
  - `test_the_report_renders_spend` (R9, including the drift misses for an old override)
  - I extended `test_retro_prints_each_change_s_numbers_only_when_asked` to cover `spend.changes`.
  - `_close()` gained a `texts=` parameter.

## Changes to `plan.md`

I filled `plan.md` in from the scaffold. After building, I added a section on where the build reads the spec its own way; those choices are the two defaults below.

## Left in `notes.md`

- [ ] R11 at ship: file the suite-pruning seed through `/sdlc:idea` on the base branch.
- [ ] `_rework()` and `_spend()` each run a `git diff -U0` per change; sharing one diff would halve those calls.

## Decisions

- DECISION: [default] Should R8's "left out of every median" apply per measure? Options: drop unrecorded changes from every median (the spec's literal wording); or drop them only from figures they can't supply. Going ahead with the second: an unrecorded change is in no tool-call figure, but its comment lines (from git) and its `out` tokens (on older `Close` commits too) still count. Recommend this because the literal reading leaves even the git-only comment view (which the intent's constraint promises when `metrics.transcripts` is off) empty until three changes close after this one.
- DECISION: [default] Should each change's own `spend` rows print only with `--metrics`? Options: always; only with `--metrics`. Going ahead with only `--metrics`, as `changes[].metrics` already works. Recommend this because of the contract that a change's own numbers print only with `--metrics`. The summary (recorded/unrecorded counts, `why`, medians, outliers, tools) always prints, so the spec's Verification step `retro | jq .spend` shows the counts and reasons rather than per-change rows unless run with `--metrics`.
- DECISION: [default] Where do added code lines come from? Options: `rec["by_kind"]` (numstat); or the same `-U0` diff the comments come from, filtered to code by `_kind()`. Going ahead with the diff: one git call gives both numbers. A suffix with no marker counts in `code_added` but not in the comment share's base (`comment_base`).

## Evidence

```
$ ./check.sh 2>&1 | grep -E "passed|failed|All checks|already formatted"   (pipefail set)
All checks passed!
247 files already formatted
2200 passed, 9 skipped in 55.52s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_metrics.py tests/test_indicators.py tests/test_retro.py -k "words_are or every_tool_call or tool_lines_round or before_tool_lines or comment_lines_by or twice_its_tier or two_changes_names or ranks_the_tools or spend_lists or renders_spend or only_when_asked or no_text_leaves_a_human"
13 passed, 260 deselected in 3.85s
exit: 0

$ uv run --group dev pytest tests/test_metrics.py -q -k "words_are or every_tool or tool_lines or before_tool"   (red, before the code)
FAILED tests/test_metrics.py::test_words_are_counted_and_no_text_leaves
FAILED tests/test_metrics.py::test_every_tool_call_is_counted_with_its_error
FAILED tests/test_metrics.py::test_tool_lines_round_trip
3 failed, 1 passed, 114 deselected in 2.03s
exit: 1

$ uv run --group dev pytest tests/test_indicators.py -q   (red, before the code)
4 failed, 31 passed in 0.10s
exit: 1

$ uv run --group dev pytest tests/test_retro.py -q -k "spend"   (red, before the code)
2 failed, 118 deselected in 3.39s
exit: 1

$ uv run --quiet --script scripts/sdlc.py retro | python3 -c "…print spend's recorded, unrecorded, why, tiers, outlier count"
{'recorded': 0, 'unrecorded': 43, 'why': {'closed before tool calls and words were counted': 43}}
{'1': {'changes': 19, 'comment_share': 0.037, 'out_per_line': 2068.1, 'tools_per_line': None}, '2': {'changes': 24, 'comment_share': 0.048, 'out_per_line': 390.541, 'tools_per_line': None}}
10 outliers
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift | python3 -c "…print breaking, refresh, report"
[] [] []
exit: 0
```
