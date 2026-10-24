---
id: 004
slug: ship-checks-base
tier: 2
impact: minor
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea:
depends_on:
serves: [O3]
---

# 004 — Catch a stale base at ship, not at close

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Change 002 (`setup-lifecycle`) failed at close. While it was open, `b50323e` ("Drop the README's
claim that the repo is private") landed on `main`, so `cmd_close()` found `main` no longer an
ancestor of the branch and refused: "main has moved past 002-setup-lifecycle's base, so it can't
fast-forward; rebase … and ship again". After the rebase the change went through the gate and the
review again, and shipped again. Its `Close` commit records the cost: `ship_runs=3`,
`ship_reruns=2`, close `segments=2 gate=2`, `stops=11` against `target=2`.

Nothing in `/sdlc:ship` asks whether the branch is behind `main`. It runs `./check.sh`, reviews
the diff and commits, all on a base that is already stale, and close is the first step that
compares the branch with `main`, after the tests and the review are spent. Any change open while
another one closes hits this, and parallel changes, one worktree each, are how the process is
meant to run.

## Outcome

- When `main` has moved past a change's base, `sdlc.py status` says so on that change's line
  (`behind main by N`), and on a shipped one under **Ready to close**.
- `/sdlc:ship` finds it at Step 0, before running the gate, and brings the branch up to date
  itself when that is clean: nothing conflicts and no work is at risk. Only when it isn't does it
  stop and say what to do. Either way, no tests or review run on a stale base.
- The same holds for a change the factory (`sdlc-factory`) built: its uncommitted edits are
  carried onto the new base, or ship stops without touching them.
- A change shipped on a current base closes on the first try; close's "main has moved past …"
  refusal fires only when `main` moved after ship.
- **Moves O3:** a change that overlaps another's close costs one ship run and no extra stop:
  `ship_reruns` in `Close` trailers stops showing reruns caused by a stale base.

## Affected

- **Area:** the ship stage's preflight, `status`, and the factory's hand-off to ship.
- **Files & components:** `scripts/sdlc.py` (`behind_main()`, shown by `status` and used by
  `cmd_close()`, plus a subcommand that updates the base or refuses), `skills/ship/SKILL.md`
  (Step 0 and its `allowed-tools`), possibly `plugins/factory/` (its build skill and
  `factory.py`), `tests/test_sdlc.py`, `tests/test_skills.py`, and `docs/REFERENCE.md`,
  `.sdlc/SDLC.md` and `defaults/SDLC.md` where they describe ship.
- **Downstream:** every host repo that runs `/sdlc:ship` or `/sdlc:status`, and every one with
  the factory installed. `status` gains a mark; ship gains a write to the branch it runs on. No
  config key, frontmatter or `work/` layout changes.
- **Contracts:** a skill's `allowed-tools` (always Tier 2); narrow `allowed-tools`, with no `if`
  in a bash block, so the branching lives in `sdlc.py`; only publish pushes; close still refuses
  rather than forces.

## Constraints

- Ship never loses work: no force, no autostash (the stash stack is shared across worktrees and
  sessions), and a rebase that conflicts is aborted, leaving the branch as it was. A refusal says
  what to do and touches nothing.
- Ship still never pushes, and close still only fast-forwards.
- The base is the local `main` in the main checkout, which is what close merges into, never a
  remote.
- No extra stop in the common case, where `main` hasn't moved.

## Open questions

- ~~Count the commits `main` is ahead, or just say "behind"?~~ Resolved: count them;
  `rev-list --count` costs the same as the ancestor test.
- ~~Ship's work is usually uncommitted at Step 0, and `git rebase` refuses a dirty tree. Is
  `git merge --ff-only main` the clean path there (the branch has no commits of its own, and git
  refuses if `main` touched a file the uncommitted work did), with `git rebase main` only for a
  clean tree whose branch has commits?~~ Resolved: yes, and a branch with commits and
  uncommitted work is refused (spec R4–R6).
- ~~Does updating the base need its own WAIT, or is it mechanical, like the gate? It rewrites
  only the change's own branch, and only when nothing conflicts.~~ Resolved: mechanical and
  reported, with the undo command, a named exception to confirm-before-writing (spec, Contracts).
- ~~Should the factory bring the base up to date before its review rounds too, so its reviewers
  see current code, or is ship's step enough?~~ Resolved: ship's step is enough for now; a
  factory-built change fast-forwards at ship (spec R9), and before review rounds is deferred.
