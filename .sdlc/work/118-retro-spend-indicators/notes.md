# Notes

- [x] R11, at ship: file the suite-pruning pass as a seed through `/sdlc:idea` (`inbox-commit`, on → seed: 2026-11-17-87
  the base branch, never this branch), carrying 2026-11-12-2's third bullet: nothing looks at the
  tests already in the suite again (one whose code was rewritten, one a newer test repeats, one
  that passes for the wrong reason, the slowest). Needs per-test run times and a test-to-code
  map no host records today (spec, *Alternatives rejected*).
- [x] `retro()` and `retro_report()` each call `_change_rows()` per change, and `_spend()` now adds → seed: 2026-11-17-88
  one `git diff -U0` per change on top; `_rework()` runs the same `-U0` diff. One diff per change
  shared between `_rework()` and `_spend()` would halve those calls. Not this change.
