# 175-pipeline-figures — entries

Retire 2026-11-19-19: taken in by 175-pipeline-figures
Retire 2026-11-19-21: taken in by 175-pipeline-figures

## [2026-11-19-53] [nit] `bisections` and `accept_stops` have no `per_change`.

Raised by the code review of 175-pipeline-figures, round 1: scripts/retro.py:1098: `bisections` and `accept_stops` have no `per_change`. `gates` and `base_moves` do. This is optional and the spec doesn't ask for it.

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 175-pipeline-figures (correctness)
