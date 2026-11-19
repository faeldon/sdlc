# 168-work-mix-and-follow-through — entries

Retire 2026-11-18-64: taken in by 168-work-mix-and-follow-through
Retire 2026-11-18-65: taken in by 168-work-mix-and-follow-through
Retire 2026-11-18-97: taken in by 168-work-mix-and-follow-through

## [2026-11-19-13] [idea] Break retro throughput down by work class

Left undone by 168-work-mix-and-follow-through, carried forward when it landed: `docs/RETRO-SCORECARD.md` *Supporting: throughput* still says "by impact S2": the work classes now exist, but throughput isn't broken down by them. A later change (S14's report, or its own) can add `process.throughput` by `work` class.
See .sdlc/work/168-work-mix-and-follow-through/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-14] [idea] Teach _milestone_verdicts() that a seed retired by inbox-commit is dropped, not vanished

Left undone by 168-work-mix-and-follow-through, carried forward when it landed: Follow-through's milestone `done` by grouped rows reads `_milestone_verdicts()` against the current register, so a grouped seed retired with `inbox-commit` reads `vanished` there (and the milestone `carried`), while the same seed scored as a seed reads `dropped`. Teaching `_milestone_verdicts()` about `Retire` subjects would change what `direction.milestones` reports, which the spec's boundaries say asks first.
See .sdlc/work/168-work-mix-and-follow-through/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-15] [nit] `_is_process` also skips `.sdlc/setup.json` (`sdlc.MANIFEST`), which R3 doesn't list.

Raised by the code review of 168-work-mix-and-follow-through, round 1: scripts/retro.py:377: `_is_process` also skips `.sdlc/setup.json` (`sdlc.MANIFEST`), which R3 doesn't list. The path is under `.sdlc/` anyway. The skip only stops a change that touched just `setup.json` from counting as process work. REFERENCE.md says so, but the spec doesn't. Drop the skip or add it to the spec.

Theme: docs
Paths: scripts/retro.py
Cost: S
Value: low
Raised by: 168-work-mix-and-follow-through (correctness)

## [2026-11-19-16] [nit] the new `bg` regex counts an unquoted `&` inside a URL such as `curl x?a=1&b=2`.

Raised by the code review of 168-work-mix-and-follow-through, round 1: scripts/metrics.py:746: the new `bg` regex counts an unquoted `&` inside a URL such as `curl x?a=1&b=2`. That is a real background `&` in shell, so this is correct, but a test case for it would pin the choice.

Theme: tests
Paths: scripts/metrics.py
Cost: S
Value: low
Raised by: 168-work-mix-and-follow-through (correctness)

## [2026-11-19-17] [nit] `test_retro_and_its_report_show_the_same_figures` compares only work mix and time to users with the report, and has no assertion on the follow-through sentence.

Raised by the test review of 168-work-mix-and-follow-through, round 1: tests/test_retro.py:2126: `test_retro_and_its_report_show_the_same_figures` compares only work mix and time to users with the report, and has no assertion on the follow-through sentence. The spec asks that the report and the JSON not disagree. The other test checks the report text, but follow-through is checked only in the JSON tests.

Theme: tests
Paths: tests/test_retro.py
Cost: S
Value: med
Raised by: 168-work-mix-and-follow-through (correctness)

## [2026-11-19-18] [nit] R14 (the docs) has no test, as the spec says.

Raised by the test review of 168-work-mix-and-follow-through, round 1: tests/test_retro.py: R14 (the docs) has no test, as the spec says. Nothing here checks that `REFERENCE.md` and the retro skill's Step 0 name the three keys.

Theme: docs
Paths: tests/test_retro.py
Cost: S
Value: low
Raised by: 168-work-mix-and-follow-through (correctness)
