# 176-by-way-of-building — entries

Retire 2026-11-19-15: taken in by 176-by-way-of-building

## [2026-11-19-59] [idea] Floor by_way throughput at a week, or leave per_week null under a week

Left undone by 176-by-way-of-building, carried forward when it landed: `by_way.throughput` floors the window at one day, as R5 says, so a retro run the day after the last retrospective gives `weeks: 0.1` and per-week figures many times the real rate (this repo, today: 196 factory changes a week over 1 day). A floor of one week, or `per_week` null under a week, would read better; it changes R5, so it is the person's call.
See .sdlc/work/176-by-way-of-building/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-60] [nit] `introducer_way()` rescans `history` for every attributed bug and every way.

Raised by the code review of 176-by-way-of-building, round 1: scripts/retro.py:3222: `introducer_way()` rescans `history` for every attributed bug and every way. This is fine at today's sizes, but a name-to-way dict built once would be simpler

Theme: refactor
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 176-by-way-of-building (correctness)
