---
id: 040
slug: factory-eval-and-review
kind: plan
created: 2026-11-04
updated: 2026-11-04
---

# 040 — Replay the factory's reviewers on escaped bugs, and review old code on request · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

Read before planning: `factory.py` as 039 left it (`_git`, `names_change`, `_base`, `_sensitive`,
`_changed_paths`, `risk_paths`), the factory spec skill's frontmatter, `skills/bug/SKILL.md`
(`bugs --introduced`, `next-entry`, `inbox-commit` taking ids), `sdlc.py`'s `bug_entries`,
`_on_paths` and `metrics.parse_trailers`, and `tests/test_skills.py`'s writing-skill set.

- `plugins/factory/scripts/factory.py`: `_words`, `_fixes`, `_open_bugs`, `on_paths` (R1, R2);
  `escapes` (R1); `report-dir` (R3); `score` (R4); `slice` (R6).
- `plugins/factory/skills/eval/SKILL.md` (new) (R5, R9).
- `plugins/factory/skills/review/SKILL.md` (new) (R7, R9).
- `skills/bug/SKILL.md`: from a report (R8).
- `plugins/factory/README.md`, `AGENTS.md`, `docs/REFERENCE.md` (R10).
- `.sdlc/work/inbox.md` at ship (R11).
- Tests: `tests/test_factory.py`, `tests/test_skills.py`.

## Work order

1. Parsing copies and `escapes`; tests, pinned comparisons included.
2. `report-dir` and `score`; tests.
3. `slice`; tests.
4. The two skills and the bug skill's report path; skill tests.
5. Docs; `./check.sh` with its exit code read directly.

## Tests

- R1, R2: scratch repos with `Close` commits carrying `Sdlc-Fixes` (with and without `paths=`) and
  `Sdlc-Base`, and a register with open bugs; the copies equal `sdlc`'s on fixtures.
- R3, R4: `report-dir` leaves `git status` clean; `score` caught, missed, unknown, comparison.
- R6: named, sensitive, stale, and an open change worktree's paths left out.
- R5, R7–R9: skill text and frontmatter tests; the invariant tests once the skills join the
  writing set.
- R10, R11: read at ship.

## Rollback

`git revert` of the ship commit. Not undone: `.sdlc/reports/` folders a host made (ignored, safe to
delete by hand). Seeds -13 and -14 would be refiled by hand (`/sdlc:idea`).
