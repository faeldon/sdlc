# 189-retro-insights — entries

Retire 2026-11-19-65: taken in by 189-retro-insights
Retire 2026-11-19-66: taken in by 189-retro-insights

## [2026-11-20-24] [idea] Lead-time-by-way scorecard rows name their real reason

Left undone by 189-retro-insights, carried forward when it landed: The scorecard's lead-time rows by way still say `none in the window` when the window closed changes but none of that way (`test_a_figure_with_no_data_reads_a_dash_with_its_reason` pins it): R11 named four blocks, not `process.lead`'s ways. `no <way> change in the window` would match the escape rate's.
See .sdlc/work/189-retro-insights/notes.md in its commit.
Raised 2026-11-20.

## [2026-11-20-25] [nit] the lead-time-by-way rows still say `none in the window` when the window closed changes but none of that way.

Raised by the code review of 189-retro-insights, round 1: .sdlc/work/189-retro-insights/notes.md: the lead-time-by-way rows still say `none in the window` when the window closed changes but none of that way. R11 named four blocks and not `process.lead`'s ways, so this is outside the spec. Ship will give it a disposition.

Theme: robustness
Paths: .sdlc/work/189-retro-insights/notes.md
Cost: S
Value: low
Raised by: 189-retro-insights (correctness)

## [2026-11-20-26] [nit] the `test_config_reports_the_insights_doc` "off while it doesn't exist" assertion only checks that no warning mentions INSIGHTS, so it is weak

Raised by the test review of 189-retro-insights, round 1: tests/test_retro.py:4867: the `test_config_reports_the_insights_doc` "off while it doesn't exist" assertion only checks that no warning mentions INSIGHTS, so it is weak

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 189-retro-insights (correctness)
