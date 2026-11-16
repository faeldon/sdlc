# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## On this repo

`sdlc.py retro --report` on 2026-11-16, window since 2026-11-04: 25 changes closed (8 tier 1, 17
tier 2), all measured. Median elapsed 1h 0m (tier 1) and 1h 1m (tier 2); agent share 0.17, since
41h 41m of away time (overnight gaps) sits beside 10h 20m of agent time. Capacity: 16 changes ran
alone (median elapsed 58m), 5 beside one other (1h 4m), 4 beside two or more (2h 54m), so the
three-at-once stretch this session ran did cost elapsed time, on four changes. Rework: 3 declared
links, 36 questions. Escapes: 5 reported and fixed, rate 0.12 against 0.0 before.

## Departures from the seed

- The seed sketched "the human's wait time against agent time" as one view; the report gives the
  four clocks per tier and an agent share over agent, response and away. Away holds overnight
  gaps, so the share is low on any window with sessions left open: read it beside the per-tier
  medians, never alone.
- Capacity's spans are estimated from what close already records (the `Close` commit's time less
  `elapsed`), not a new trailer; `days_open` was useless for it (0 for most changes).
- A dashboard stays out, as the seed allowed.
