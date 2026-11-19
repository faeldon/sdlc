# Notes

- [x] `docs/RETRO-SCORECARD.md` *Supporting: throughput* still says "by impact S2": the work → seed: 2026-11-19-13
  classes now exist, but throughput isn't broken down by them. A later change (S14's report, or
  its own) can add `process.throughput` by `work` class.
- [x] Follow-through's milestone `done` by grouped rows reads `_milestone_verdicts()` against → seed: 2026-11-19-14
  the current register, so a grouped seed retired with `inbox-commit` reads `vanished` there
  (and the milestone `carried`), while the same seed scored as a seed reads `dropped`. Teaching
  `_milestone_verdicts()` about `Retire` subjects would change what `direction.milestones`
  reports, which the spec's boundaries say asks first.
