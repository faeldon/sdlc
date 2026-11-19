---
id: 188
slug: local-day-elapsed
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-19T21:41Z
updated: 2026-11-20
shipped: 2026-11-20
idea:
depends_on:
fixes: [2026-11-20-3]
serves: [O4, O3]
---

# 188 — Close measures elapsed from the local day, never negative

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Close's `from_history` (`scripts/closing.py`) measures a change's elapsed time as now minus its
`created:` date read as midnight UTC: `datetime.combine(created, dtime(), UTC)`. But `created:`
is the local day `new` stamped (`date.today()`). On a machine east of UTC, between local midnight
and UTC midnight, a change created that local day starts in the future, so the
`Sdlc-Totals: elapsed=` trailer on its `Close` commit is negative. At UTC+8 that window is 00:00
to 08:00 local, every day.

It also turns this repo's gate red for those hours. `tests/test_archive.py`'s
`test_close_output_is_unchanged` pins close's output, and four of its cases (shipped, dropped,
rerun, pushed) then read `elapsed=-N`. On 2026-11-20 the landing gate failed on them and ejected
187-one-word-one-meaning, whose own diff was sound. The same four fail on `main`.

## Outcome

- Close measures from the start of the `created:` day in the machine's own timezone, so
  `elapsed` is never negative, whatever the hour or the timezone.
- `test_close_output_is_unchanged` passes at any hour: its clock and timezone are pinned, not
  read from the machine.
- A new test fails if a change created on the local day, closed in the window where that day is
  ahead of UTC, measures a negative elapsed.
- **Moves O4:** the `Sdlc-Totals` figures the retrospective reads are never negative, so their
  medians can be trusted.
- **Moves O3:** the gate no longer goes red for eight hours a day and ejects sound landings.

## Affected

- `scripts/closing.py` (`from_history`), on the sensitive list, so it gets the full review.
  Possibly `scripts/metrics.py`, if elapsed is clamped there.
- `tests/test_archive.py`, and `tests/fixtures/` if the pinned close output changes.
- **What reads it:** close's `measure` step writes `Sdlc-Totals` onto every `Close` commit;
  `/sdlc:retro` and the board read those trailers. Hosts east of UTC get correct figures from now
  on. Figures already committed stay as they are.

## Constraints

- The metrics trailer contract (`scripts/metrics.py`'s docstring) is extended, never redefined:
  `elapsed` keeps its name and unit.
- Measuring never refuses: a close still lands even when it can't measure.
- No change to closes measured from transcripts. Only the history fallback is wrong.
- Windows: no new platform-only import, and dates are handled the same way on every OS.

## Approach

In `from_history`, take the start as midnight of `created` in the local timezone
(`datetime.combine(created, dtime()).astimezone()`), compared with `datetime.now(UTC)`, and
never let it fall after now. Pin `test_close_output_is_unchanged` to a fixed clock and timezone
the way `_Frozen` already pins `CLOSED_AT` for the lead-time tests. Add a test that sets the
timezone to UTC+8 and the clock to 02:00 local on a change's `created:` day, and asserts
`elapsed >= 0`.

## Open questions

- Should `new` stamp `created:` in UTC instead, so every date in the record shares one clock?
  That would change what the intent's date means for a host.
