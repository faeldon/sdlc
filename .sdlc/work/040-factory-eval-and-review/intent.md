---
id: 040
slug: factory-eval-and-review
tier: 2
impact: minor
stage: shipped
created: 2026-11-04
updated: 2026-11-04
shipped: 2026-11-04
idea: 2026-11-03-13
depends_on:
serves: [O4]
---

# 040 — Replay the factory's reviewers on escaped bugs, and review old code on request

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The factory's reviewers are tuned by guesswork, and only ever look at the change in front of them:

- **A change to a reviewer's prompt or model is a guess.** 037 traces each escaped bug to the
  change that let it in, and that change's diff is in history, but nothing replays the factory's
  reviewers (`plugins/factory/agents/reviewer-*.md`) on those diffs to ask whether they'd catch the
  bug now. A prompt edit or a `factory.toml` model swap can make review worse unseen.
- **Old code is reviewed only when a change trips on it.** 038's `PREEXISTING` lines catch problems
  next to a change, nothing more. Code no change touches, often the paths `[review] sensitive`
  names, is never reviewed until a bug is filed against it.

This takes in seeds 2026-11-03-13 and -14, the last of the code-review series. Their designs were
agreed at 039's spec and are written on the seeds: the eval reads the diff as text and files at the
commit with `git show`, and a reviewer caught a bug when a `CHANGE:` of its sits on the bug's
paths, each shown for the person to judge; the review writes an uncommitted report of proposed
`[bug]` entries that `/sdlc:bug` files through `inbox-commit` behind its own WAIT, run when asked,
with `/schedule` shown in the README.

## Outcome

- `factory.py eval` lists every escaped bug with an introducing change (fixed ones from
  `Sdlc-Fixes`, open ones from the register), each with its paths and the introducing change's
  commit and diff.
- `/sdlc-factory:eval` replays the configured reviewers on each diff, as text, read-only, and
  reports per bug which reviewers raised a `CHANGE:` on its paths (those lines shown), and a score
  per reviewer: a prompt or model change is kept only when the score holds or rises. Run when asked,
  writing nothing to the repo, no WAIT.
- `/sdlc-factory:review` reviews a slice of code no open change touches (the `[review] sensitive`
  paths, or the least recently changed) and, behind one WAIT, writes an uncommitted report of
  proposed `[bug]` entries in the shape `/sdlc:bug` files; it fixes nothing and files nothing.
- `/sdlc:bug <report>` files the entries the person picks from such a report, each with its own id,
  through `inbox-commit` behind its one WAIT: one path into the register still.
- Seeds 2026-11-03-13 and -14 both leave the register when this ships.
- **Moves O4:** a change to how the factory reviews (a prompt, a model, a reviewer added) is kept or
  reverted on the eval's score against real escaped bugs, not on judgment.

## Affected

- **Area:** the optional `sdlc-factory` plugin, and `sdlc`'s `/sdlc:bug`.
- **Files & components:** `plugins/factory/scripts/factory.py` (`eval`, reading trailers and the
  register itself), two new factory skills (`eval`, `review`), `skills/bug/SKILL.md` (taking a
  report), `plugins/factory/README.md`, `AGENTS.md`, `docs/REFERENCE.md`, tests in
  `test_factory.py`, `test_skills.py` and `test_bugs.py`.
- **Downstream:** hosts that install `sdlc-factory` gain two skills; hosts without it see nothing.
  Every host's `/sdlc:bug` gains the report path, unchanged without one.
- **Contracts:** `inbox-commit` is the only code that commits the inbox; release, publish and
  measuring never read the register (a factory command reading it is none of those); the factory's
  cached copy has no `sdlc.py`, so `factory.py` copies what it parses, pinned by a test; agents that
  judge have no `Write`, nothing commits; one WAIT per writing skill, narrow `allowed-tools`;
  metrics trailers read, never redefined.

## Constraints

- Nothing in the eval checks out, stashes or writes under `.git/`: a replayed diff is text, files at
  a commit read with `git show`.
- Bugs reach the register only through `/sdlc:bug` and `inbox-commit`.
- An escape without paths (a trailer from before 037) is listed but scored unknown, never missed.

## Open questions

- ~~How `factory.py` reads escapes without `sdlc.py`: copy `metrics.parse_trailers`'s
  `Sdlc-Fixes` and the register's bug-entry parsing, each pinned by a test? And the introducing
  change's diff from its `Close` commit's parent against `Sdlc-Base:`?~~ Resolved: copies pinned
  by tests; the diff from `Sdlc-Base:` to the close's parent, else the parent's own, `partial`
  (spec R1, R2).
- ~~Is the eval's report kept (a file per run, `.sdlc/evals/<date>.md`, uncommitted) so the next
  run compares against the last, or printed only and compared by hand?~~ Resolved: kept in a
  self-ignoring `.sdlc/reports/`, each run compared with the last, the person's call (spec R3, R4).
- ~~What bounds an eval or a review run (bugs replayed, paths reviewed, agent runs), and does each
  skill state it before it starts, as the build does?~~ Resolved: `--limit` (default 10), the most
  agent runs stated at one WAIT each, the person's call (spec R5, R7).
- ~~The review's slice: how many paths, chosen how ("least recently changed" by `git log`), and are
  paths an open change touches left out?~~ Resolved: sensitive paths, else the least recently
  changed, open changes' paths left out, or named paths, the person's call (spec R6).
- ~~The report's shape: the exact format `/sdlc:bug` reads (`## [?] [bug] title` blocks with
  `Severity:`, `Paths:`, an offered `Introduced by:`), and where it lives.~~ Resolved: `## [?]
  [bug]` blocks with `Severity:` and `Paths:` in `.sdlc/reports/review-…/review.md`;
  `/sdlc:bug` gives ids and offers `Introduced by:` (spec R7, R8).
