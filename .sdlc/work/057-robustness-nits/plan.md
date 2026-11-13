# 057 — Pay down the robustness nits

## Context

Eight `[robustness]` nits (seed 2026-10-26-7, priority high) each make `status`, `close --check`,
`retro`, a failed release, intent's issue intake or the factory's review report something false or
late. One fix and one test per nit, in `scripts/sdlc.py`, two skills, and tests. Tier 1.

Open questions, resolved by reading the code:
- **26-1 and the WAIT:** `sync` already makes each `closes:` issue a sub-issue on intent's yes, and
  `mark-triaged` already comments on an *uncommitted* `closes:` (test
  `test_mark_triaged_points_an_attached_issue_at_its_change`), so the comment from `sync` is the
  same kind of write behind the same yes, worded by core's `recorded_issues()`. The WAIT question
  doesn't change: stays Tier 1.
- **25-13, which shipped titles:** the ones `next_up` already uses for its `⚠` warning:
  `closed_changes()`' `idea:`s on main's first-parent line, matched with `same_ref()`.

## Fixes (scripts/sdlc.py unless named)

1. **2026-10-25-13 `next_up`:** compute `unmet` (an `After:` title in no register entry and no
   shipped change's `idea:`) once, before the rules loop, reusing the existing
   `closed_changes(...)`/`same_ref` block (moved up, still only run when something dangles). The
   `series` rule then also requires `not any(t in unmet for t in e["after"])`; the warning loop
   uses the same `unmet`. Such a seed falls to the plain `idea` rule.
2. **2026-10-25-14 `_after_loops`:** follow every waiting title, not the first. For each waiting
   seed, the set it can reach through waiting titles; a seed that can reach itself is in a loop,
   whose members are the seeds it reaches that reach it back, listed in register order, each loop
   once. Same signature and output for the existing test.
3. **2026-10-25-17 `cmd_release`:** keep after-bump's `before` (untracked set) in the closure;
   `restore()` recomputes `report["untracked"] = sorted(_untracked(home) - before)` when after-bump
   has run, so a later prepare/commit failure names the file it unstaged.
4. **2026-10-26-1 `cmd_sync`:** after a sync without error, when the change has `closes:` and
   `_intake_tracker()` finds a tracker, run `mark_issues(home, found, only=set(closes))` (new
   optional `only` parameter filtering `records`), adding its `done` to the report's `done` and
   its `failed` to `skipped`: never fatal. `skills/intent/SKILL.md` Step 5's sentence on `sync`
   says it now also tells each filer (no change to Step 4's question).
5. **2026-10-27-4 `cmd_close`/`_reaches`:** `_reaches(main, branch, start=None)` uses `start`
   when given; close passes `tip` under `--check` when the change hasn't landed (the ref close
   would write), else None.
6. **2026-11-04-2 `_review_at`:** return `problems` (from `_findings_from_text`'s second value)
   beside `findings`; the unknown default in `bugs_retro` gets `"problems": []`. A change whose
   file has problems also counts in `important_unknown`. Update the one phrase in
   `docs/REFERENCE.md` and `skills/retro/SKILL.md` (`important_unknown`: no `findings.md`, or one
   that no longer parses; `review.problems`).
7. **2026-11-04-5:** `plugins/factory/skills/review/SKILL.md` — when the host's process doc has no
   section on bugs, leave the `Severity:` line out; `skills/bug/SKILL.md`'s "From a report"
   paragraph asks for a severity a block lacks.
8. **2026-11-08-2 `last_touched`:** when the change's checkout is the main checkout
   (`main_root(root)`), keep only dirty paths under the change's own folder.

## Tests

- `tests/test_next_up.py`: a seed with a mistyped `After:` is `idea`, not `series`, and still
  warns; a loop through a second `After:` title is warned; a main-checkout change folder isn't
  touched by an unrelated dirty file.
- `tests/test_release.py`: after-bump stages a new file, prepare then fails → `untracked` names it.
- `tests/test_archive.py`: `sync` comments "Taken on by" on a `closes:` issue once (rerun adds
  nothing); `close --check` on the first-commit-without-folder case reports the same `reaches`.
- `tests/test_bugs.py`: a findings.md with a malformed section gives `review.problems` and counts
  in `important_unknown`; existing exact-dict assertion gains `"problems": []`.

## Then

Save this plan as `.sdlc/work/057-robustness-nits/plan.md`, set `stage: build`, implement, and run
`./check.sh`. Ship is `/sdlc:ship`, run separately.

## Verification

`uv run --group dev pytest -q tests/test_next_up.py tests/test_release.py tests/test_archive.py
tests/test_bugs.py`, then `./check.sh` (ruff, format, full pytest, plugin validate).
