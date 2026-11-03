---
id: 040
slug: factory-eval-and-review
kind: spec
created: 2026-11-04
updated: 2026-11-04
---

# 040 — Replay the factory's reviewers on escaped bugs, and review old code on request · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. Escapes, listed.** `factory.py escapes [--limit N]`, read-only: each escaped bug with an
   introducing change, from the base branch's `Close` commits' `Sdlc-Fixes` lines (fixed) and the
   register's `[bug]` entries with `Introduced by:` (open), newest reported first, up to `N`
   (default 10). Each carries its id, title (null for a fixed one), paths (null when none were
   recorded), the introducing change's name and commit, its `base` (that `Close` commit's
   `Sdlc-Base:`, else the commit's parent), and `partial: true` when there was no `Sdlc-Base:`.
   Escapes whose introducing change names no closed change are counted in `unknown_change`. Tests:
   a fixed escape, an open one, a pathless one, an unknown change.
2. **R2. Pinned copies.** `factory.py`'s `Sdlc-Fixes` parsing matches `sdlc.metrics.parse_trailers`
   on a table of lines; its bug-entry fields match `sdlc.bug_entries` on a register fixture; its
   `on_paths` matches `sdlc._on_paths` on 037's cases.
3. **R3. Reports folder.** `factory.py report-dir --kind eval|review` creates `.sdlc/reports/` with a
   `.gitignore` of `*`, then a fresh run folder `eval-<date>-<n>/` or `review-<date>-<n>/`, and
   prints its path. `git status` stays clean after it (a test). Nothing else is written.
4. **R4. Scoring.** `factory.py score <run-dir>` reads each `<bug>/<role>.md` reply: a reviewer
   caught a bug when a `CHANGE:` of its sits on the bug's paths; with the paths unknown, the result
   is `unknown`, never `missed`. It writes `<run-dir>.md`: per bug, each reviewer's result and the
   lines that caught it; per reviewer, `caught` of `scored`; compared with the newest earlier
   `eval-*.md`, each reviewer's change in score. Tests: caught, missed, unknown, the comparison.
5. **R5. `/sdlc-factory:eval`.** A new skill: Step 0 runs `factory.py config` and `escapes`, shows
   the bugs, the configured reviewers and the most agent runs (bugs × reviewers). **One WAIT:**
   `Replay <reviewers> on the introducing diffs of these <N> escaped bugs, at most <runs> agent
   runs, and write the scores under .sdlc/reports/? (yes / change the limit / no)`. After yes:
   `report-dir --kind eval`, writes `escapes.json` there, spawns each reviewer per bug with
   `Replay: review the change <name>: run git diff <base> <commit>, read files at <commit> with git
   show; write nothing.`, writes each reply to `<bug>/<role>.md`, then `score`. It never edits code,
   commits, checks out or stashes.
6. **R6. Slice.** `factory.py slice [--paths P …] [--limit N]`, read-only: the paths to review: the
   named ones; else tracked files under the base branch's `[review] sensitive`; else the `N` least
   recently changed tracked files (one `git log --name-only` walk); minus any path an open change
   worktree's diff touches; with `why`. Tests: each source, and the open-change exclusion.
7. **R7. `/sdlc-factory:review`.** A new skill: Step 0 runs `config` and `slice`, shows the paths,
   the reviewers (`code`, `security`) and the most agent runs. **One WAIT:** `Review these <N>
   paths with <reviewers> as they stand, at most <runs> agent runs, and write the problems found as
   proposed bugs to .sdlc/reports/? (yes / change the paths / no)`. After yes: `report-dir --kind
   review`, spawns each reviewer with `No change: review the code at <paths> as it stands; return
   each problem as - PREEXISTING: path:line: what.`, and writes `review.md`: one `## [?] [bug]
   <title>` block per distinct problem, with what's wrong, a proposed `Severity:` from the process
   doc's words, and `Paths:`. It fixes and files nothing; its report ends with
   `/sdlc:bug .sdlc/reports/review-…/review.md`.
8. **R8. `/sdlc:bug <report>`.** Given a report's path, the bug skill lists its `[?]` entries, the
   person picks which to file, it takes ids with `next-entry --count <n>`, offers each one's
   `Introduced by:` as today, shows them, and asks its one WAIT: `Append these <n> bugs to
   .sdlc/work/inbox.md as <ids> and commit them as "File <ids>"? (yes / edit them / no)`, filing
   them through one `inbox-commit`. With no report, it is exactly as now. A skill test pins the path
   and the single WAIT.
9. **R9. The skills' contracts.** Both new skills: `allowed-tools` naming exactly their `factory.py`
   commands plus `Agent`, `Read`, `Write`; a description saying when not to use them; one WAIT
   heading each; `READS_CONFIG` entries. The judging agents keep their tools.
10. **R10. Docs.** `plugins/factory/README.md` (the two skills, `.sdlc/reports/`, putting the review
    on `/schedule`), `AGENTS.md`'s factory paragraph (the pinned copies; the factory never writes
    the register), `docs/REFERENCE.md` (`/sdlc:bug` takes a report).
11. **R11. Seeds.** At ship, 2026-11-03-13 leaves through `idea:`; -14 deleted by hand.

## Design

- **Factory reads history itself.** `_fixes(root, base)` walks `git log --first-parent
  --format=%H%x00%P%x00%B base` for `Close <name>` subjects, parsing `Sdlc-Fixes:` and
  `Sdlc-Base:` lines with a copied word parser, and the close's parent as the change's commit.
  `_open_bugs(root)` parses `.sdlc/work/inbox.md` headings and `Key: value` lines, `[bug]` only.
  Escapes are matched to a close by `names_change()` (already copied).
- **Reports.** `report-dir` writes `.sdlc/reports/.gitignore` (`*`) if missing, and run folders
  numbered within the day. `score` reads the run's `escapes.json`, which the skill writes from
  `escapes`' output, so scoring never re-walks history.
- **Agents.** No new agents: the reviewers already return `CHANGE:` and `PREEXISTING:` lines and
  have `Bash` for `git diff` and `git show`; the prompts are the skills', each saying write nothing.
- **The bug skill.** A "From a report" branch in Steps 1 and 3, Step 4's question in its plural
  form, and Step 5's `inbox-commit` with each id from a worktree (none from the main checkout).

## Contracts touched

- **`inbox-commit` is the only code that commits the inbox:** reports reach the register only
  through `/sdlc:bug` and it; `factory.py` never writes the register.
- **Release, publish and measuring never read the register:** `escapes` is none of those.
- **The factory's cached copy has no `sdlc.py`:** the copies are pinned by tests, as 038's matcher.
- **Nothing under `.git/`, no checkout, no stash:** diffs are `git diff` text, files `git show`.
- **Agents that judge have no `Write`; nothing commits:** unchanged.
- **One WAIT per writing skill, narrow `allowed-tools`:** each new skill has one; the bug skill
  keeps its one.
- **Metrics trailers read, never redefined:** `Sdlc-Fixes` and `Sdlc-Base` read.

## Alternatives rejected

- **`/sdlc:setup` ignoring `.sdlc/reports/`:** touches setup, its record and uninstall; a folder
  that ignores itself needs none of them.
- **A scratch worktree per escape:** writes under `.git/worktrees` (decided at 039).
- **A new auditor agent for the review:** the code and security reviewers already return
  `PREEXISTING:` lines.
- **`factory.py` appending bugs to the register:** a second path into it (decided at 039).

## Verification

- `./check.sh`, its exit code read directly.
- `uv run --group dev pytest tests/test_factory.py tests/test_skills.py tests/test_bugs.py -q`,
  cases for R1–R4, R6, R8, R9.
- `factory.py escapes` on this repo lists nothing (no bugs yet); `factory.py slice` lists the files
  under this repo's sensitive paths.
