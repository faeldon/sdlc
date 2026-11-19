# Notes

- [x] `render_report()` now takes eight positional blocks and five keyword ones. One figures dict → seed: 2026-11-19-63
  (`report_figures()`'s) passed whole would read better, but the tests' many
  `render_report(template, process)` calls would all change with it, so it stays out of 184.
- [x] A scorecard row whose block has no `missing_because` (response by tier, autonomy, the → seed: 2026-11-19-64
  workarounds) says `none in the window` when null, even when the window held changes that just
  weren't measured: R5's rule as written. A per-row reason would need those blocks to carry one.
