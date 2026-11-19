DECISION: READY

**Why.** All four round-1 reviewers (code, security, test, behaviour) returned `VERDICT: PASS` with no Critical, High or required findings, and the gate is green: `./check.sh`, exit 0, 3413 passed. Each of the intent's three outcomes has a test. The builder ran the new tests against the old `closing.py`, and exactly the four failing cases from 2026-11-20 failed, plus the new local-day test. The behaviour reviewer then re-ran them under `TZ=Asia/Singapore` and `TZ=Pacific/Kiritimati`. The fix follows the intent's Approach line for line: `_day_start()` takes local midnight of `created:`, clamps it to `now`, and falls back to UTC midnight when the platform can't place the date, so measuring still never refuses. Closes measured from transcripts and the `metrics.py` trailer contract are untouched.

**Open items**
- None. The only findings are two NITs, both recorded and neither open:
  - F1 (code): add a comment on the `east` fixture saying it must not be marked `portable`.
  - Test: a direct unit test of `_day_start()` would cover the clamp, a missing `created:` and a timezone west of UTC.

**Decisions to confirm**
- No blocking decisions are unticked.
- SETTLED: D1: the intent's own Approach (intent.md, line 66) fixes the measurement and leaves the stamp alone, and none of its Outcomes needs `new` to change. The built code (`scripts/closing.py: _day_start()`) follows this and changes nothing about what a host's `created:` means. Moving `new` to stamp in UTC would change a host-facing date and would need its own change, which the person can still start from the intent's open question.

**For the person at ship**
- Look first at `scripts/closing.py: _day_start()` (lines 403–414) and where it is called in `measure_change`'s `from_history` (line 485). This file is on the sensitive list, and this is the whole fix.
- Then look at the `east` fixture and `_pin_clock()` in `tests/test_archive.py`, around line 2497. The fixture sets `TZ`, calls `time.tzset()` (POSIX only) and puts the timezone back afterwards. The tests that use it are rightly not marked `portable`.
- The change touches no published interface. `Sdlc-Totals: elapsed=` keeps its name and unit, and only its value is now correct east of UTC.
- The intent's open question (D1) stays the person's to reopen if they want every date on UTC.

- IMPACT: patch — hosts east of UTC no longer get a negative `elapsed` on closes in the hours after local midnight. Nothing new to do or learn.

**Undone items**
- None. There is no `notes.md`, and the builder reports nothing left over.
