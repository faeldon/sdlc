---
id: 037
slug: escaped-bugs-tune-review
kind: plan
created: 2026-11-04
updated: 2026-11-04
---

# 037 — Retro tunes the review from the bugs that got past it · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

Found reading the code: `Sdlc-Fixes` (`fix_trailers()`) carries severity, reported and
introduced_by only, so a fixed bug's paths are lost once ship deletes its entry, and its title
isn't there either (`escaped[].title` is null for a fixed bug). `findings_entries()` reads from
disk; `closed_changes()` already reads each change's `Sdlc-Findings` from its own commit;
`bugs_retro()` already builds `history` over every closed change; `last_retrospective()` returns
only the newest boundary.

- `scripts/sdlc.py`
  - `fix_trailers()`: append `paths=<p1>,<p2>` from `Paths:` (split, stripped as `bug_entries()`
    does), `paths=unknown` when none (R1).
  - `_findings_from_text(text)` extracted from `findings_entries()`, which keeps its output (R2).
  - `_review_at(home, name, sha, counts)`: `findings.md` from the change's own commit; `state`
    `file` / `trailer` / `unknown`, `counts`, `findings` (R2).
  - `_on_paths(evidence, paths)`: equal, under, or containing; None for unknown paths (R3).
  - `retrospectives(home, trunk)` newest first; `last_retrospective()` its first (R4).
  - `bugs_retro()`: fixed bugs from all of history for the rate; each escape gains `escaped` and
    `review`; new `rate` (`RATE_MIN_CHANGES = 5`), `important`, `important_unknown` (R2–R5, R9).
- `skills/retro/SKILL.md`: Step 0's `bugs` bullet; the Process pass's bugs paragraph for R6–R7;
  Step 3's Seed bullet (exact text in the seed); Out of scope names the review doc and
  `.sdlc/config.toml`. No new tools or commands (R6–R8).
- `guide/review.md`: the "ways this repo's code fails" slot says retro proposes leads from
  escapes; then `scripts/sdlc.py record` (R10).
- `docs/REFERENCE.md`: `Sdlc-Fixes` `paths=`; retro's `bugs` keys (R10).
- `AGENTS.md`: the Bugs paragraph names the pairing (R10).
- `.sdlc/work/inbox.md` at ship: delete -8, -9's `After:` line, -13's `After:` to `2026-11-03-12`
  (R11).
- Tests: `tests/test_bugs.py`, `tests/test_retro.py`, `tests/test_findings.py`,
  `tests/test_skills.py`.

## Work order

1. `_findings_from_text`, `fix_trailers` paths; tests.
2. `retrospectives()`, `_review_at`, `_on_paths`, `bugs_retro()` extensions; tests.
3. Retro skill; skill tests.
4. Guide, REFERENCE, AGENTS.md; `record`; `./check.sh` with its exit code read directly.

## Tests

- R1: `test_bugs.py`: `fix_trailers` lines with `paths=` and `paths=unknown`; a trailer without
  `paths` reads as unknown.
- R2: `test_retro.py`: an escape whose change has `findings.md` → `file`; a trailer only →
  `trailer`; neither → `unknown`.
- R3: `_on_paths` on a file, a directory prefix, a containing path, no match, None.
- R4: `retrospectives()` order; trend `up`, `down`, `flat`, `unknown` (no previous, under five
  changes); retired bugs not counted.
- R5: an Important finding listed; a change without a file in `important_unknown`.
- R8: `test_skills.py`: retro's Out of scope names the review doc and `config.toml`; its
  `allowed-tools` and `retro-commit`'s allowed set unchanged.
- R9: `test_bugs.py`'s no-bugs `retro` gains `rate`, `important`, `important_unknown`, nothing
  else.
- R6, R7, R10, R11: read at ship; `sdlc.py drift` empty.

## Rollback

`git revert` of the ship commit. Not undone: `Sdlc-Fixes` lines written meanwhile keep `paths=`,
which older code reads as an unknown field, harmlessly. Seeds -7 and -8 would be refiled by hand
(`/sdlc:idea`).
