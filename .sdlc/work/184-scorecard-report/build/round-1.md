I've built change 184 and left it uncommitted for `/sdlc:ship`: the retrospective report now opens with the scorecard, and every requirement R1–R21 has a test or an acceptance check. I reran every command the report rests on. The full gate passed: ruff, the format check, 3331 tests (29 skipped) and both plugin validations.

## Slices built
1. **Seeds and nits (R13, R15–R19):**
   - A window under a week now gives a null `per_week`, with `why: "window under a week"`.
   - Indicator rows with a `—` unit, or a name or unit with stray spaces, are now refused.
   - `bisections` and `accept_stops` now carry `per_change`.
   - `bugs_retro()` now works out each `Introduced by:` value's change once.
   - The comment on `_surface_at()` and the `_retire()` docstring explain what the spec asked for.
2. **One computation (R12):** `report_figures()` is now the only place `_cost` runs, and both `retro()` and `retro_report()` get their figures from it.
3. **One table reader (R7):** `report_rows()` now reads both the indicator table and the scorecard table.
4. **`scorecard()` (R3–R7):**
   - It builds the pillar rows the spec's table lists.
   - A missing figure reads `—` with its reason, and a thin one is marked as a hint.
   - Each row's `last` is read from the previous committed report, and its `trend` compares against it.
   - The table is also in the JSON as `scorecard`.
5. **Template and sections (R1, R2, R8–R11):**
   - The new layout: Window, Scorecard, then a section each for Speed, Quality, Indicators, Autonomy, Cost, Spend and Simplicity.
   - A host's Simplicity section shows only its workarounds.
   - An override without `{{scorecard}}` still renders as before.
   - `TEMPLATE_READS` now includes the `Scorecard` heading and the `{{scorecard}}` placeholder.
6. **Skill, docs and record (R14, R20, R21):**
   - The retro skill lists `scorecard` in Step 0, and its process pass now reads `simplicity.workarounds`.
   - REFERENCE.md describes the scorecard and the new layout.
   - S14 is marked done (184).
   - I ran `sdlc.py record` from this checkout.

## Tests
- **New tests:** `test_the_report_s_sections_come_in_order` (R1), `…_value_band_table_and_trust_band_once` (R2), `test_scorecard_rows_for_a_host_and_for_the_plugin` (R3, R4), `…_reads_a_dash_with_its_reason` (R5), `…_greyed_lead_time_is_marked_a_hint` (R6), and three tests for `last` and `trend` (R4, R7).
- **More new tests:** `…_pillar_sections_show_autonomy_pipeline_and_cost` (R8), two Simplicity tests (R9), the old-override test (R10), `…_without_the_scorecard_is_breaking` (R11), `test_report_figures_runs_cost_once` (R12), `…_null_under_a_week` (R13), the skill test (R14), four new rejection cases plus the shared table-reader test (R15), the registry tag test (R16), the `per_change` tests (R18) and `…_resolved_once…` (R19).
- **Run before the fix:** the R19 test failed with `[4, 12]` calls (one bug against three), and the scorecard and template tests also failed. Those runs aren't repeated below, because the code they failed against is gone.
- **Passed without any code change:** the R10 and R16 tests, because they pin behaviour that already existed.
- **Written after the change:** the R14 test, which I wrote just after editing the skill.
- **Existing tests updated, because the spec moved what they check:**
  - The Value band, coverage and *What changed underneath* tests now read from `## Scorecard`, and the by-way table test from `## Speed`.
  - The `score` check now looks for the whole word, because the new `Scorecard` heading contains it.
  - Two template-slicing tests now follow the new section order.
- **Acceptance checks:** three in `checks.md`, covering the R17 and R20 doc sentences. All three pass through `accept`.

## Changes to `plan.md`
A new "Where the build departed from the plan" section lists:
- `render_report()` takes the table as `card=`, because `scorecard` is already the function's name.
- A `_surface = surface` alias, needed because the `surface` flag shadows the function inside `report_figures()`.
- R14's test lives in `test_retro.py`.
- The older tests that changed.
- The template note names "the scorecard's table", not the `## Scorecard` heading. Some tests split the template on that heading, and with it in the note they cut there first.

## Left in `notes.md`
- `render_report()` now takes many arguments. Passing one figures dict instead would be cleaner, but it would mean rewriting many test calls.
- A null row whose source block gives no reason says `none in the window`, even when the window had changes that just weren't measured. That is R5 as written.

The spec's Verification also asks for `sdlc.py retro`'s JSON. I didn't run that, because this repo's `retro.test_times` reruns the whole suite; the tests check the same JSON.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_indicators.py tests/test_surface.py tests/test_skills.py tests/test_defaults.py tests/test_comment_health.py
882 passed in 78.80s (0:01:18)
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
319 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 184
All checks passed!
319 files already formatted
3331 passed, 29 skipped in 157.69s (0:02:37)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift
  "breaking": [],
  "refresh": [],
  "report": [],
exit: 0

$ grep -n "doesn't show these yet\|aren't in its body yet" docs/REFERENCE.md
exit: 1

$ uv run --quiet --script scripts/sdlc.py accept 184
  "passed": true,
  "problems": []
}
exit: 0

$ git rev-parse --short HEAD
8f6dbd5
exit: 0
