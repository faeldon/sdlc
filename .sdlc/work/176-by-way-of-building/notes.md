# Notes

- [x] `by_way.throughput` floors the window at one day, as R5 says, so a retro run the day after → seed: 2026-11-19-59
  the last retrospective gives `weeks: 0.1` and per-week figures many times the real rate (this
  repo, today: 196 factory changes a week over 1 day). A floor of one week, or `per_week` null under
  a week, would read better; it changes R5, so it is the person's call.
- `_milestone_verdicts()` walks `retired_entries()` once a call, and only when a grouped seed is
  neither shipped nor in the register, so `status` pays nothing in the usual case.
