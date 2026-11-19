# 184-scorecard-report — entries

Retire 2026-11-19-35: taken in by 184-scorecard-report
Retire 2026-11-19-42: taken in by 184-scorecard-report
Retire 2026-11-19-43: taken in by 184-scorecard-report
Retire 2026-11-19-53: taken in by 184-scorecard-report
Retire 2026-11-19-60: taken in by 184-scorecard-report

## [2026-11-19-63] [idea] Pass report_figures() to render_report() as one dict

Left undone by 184-scorecard-report, carried forward when it landed: `render_report()` now takes eight positional blocks and five keyword ones. One figures dict (`report_figures()`'s) passed whole would read better, but the tests' many `render_report(template, process)` calls would all change with it, so it stays out of 184.
See .sdlc/work/184-scorecard-report/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-64] [idea] Give response, autonomy and workarounds blocks a missing_because so scorecard rows name their real reason

Left undone by 184-scorecard-report, carried forward when it landed: A scorecard row whose block has no `missing_because` (response by tier, autonomy, the workarounds) says `none in the window` when null, even when the window held changes that just weren't measured: R5's rule as written. A per-row reason would need those blocks to carry one.
See .sdlc/work/184-scorecard-report/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-65] [nit] `_trend` compares the unrounded `value` with the `last` read back from the report's cell, which was written through `indicators.number`.

Raised by the code review of 184-scorecard-report, round 1: scripts/retro.py:423: `_trend` compares the unrounded `value` with the `last` read back from the report's cell, which was written through `indicators.number`. A figure that rounds to the same cell (for example 0.174 against a written 0.17) could read `up` when the person saw two equal numbers. Compare after rounding `value` the way the table writes it, or confirm `number()` writes full precision.

Theme: robustness
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 184-scorecard-report (correctness)

## [2026-11-19-66] [nit] `_minutes` rounds a median response to a whole number.

Raised by the code review of 184-scorecard-report, round 1: scripts/retro.py:433: `_minutes` rounds a median response to a whole number. The report above shows a median response of "1" minute in both tiers, so small values lose their trend resolution. This follows the spec's "integers" rule, so it is only worth a Note in REFERENCE.md.

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 184-scorecard-report (correctness)

## [2026-11-19-67] [nit] `test_the_pillar_sections_show_autonomy_pipeline_and_cost` checks the Speed pipeline terms as bare lowercase substrings ("gates", "bisections").

Raised by the test review of 184-scorecard-report, round 1: tests/test_retro.py: `test_the_pillar_sections_show_autonomy_pipeline_and_cost` checks the Speed pipeline terms as bare lowercase substrings ("gates", "bisections"). It would still pass if they appeared anywhere in the Speed section, such as in prose rather than the landing line. Match the landing line's label instead.

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 184-scorecard-report (correctness)
