---
id: 077
slug: ship-resolves-conflicts
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
serves: [O3]
---

# 077 — Ship resolves a conflict with the base branch itself

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

When `main` has moved under a change, `/sdlc:ship` stops and hands the conflict to the person, and
the person's answer is the same every time.

`sdlc.py base` (`cmd_base()`, `scripts/sdlc.py:3278`) refuses in two cases:

- a branch with no commits of its own whose uncommitted work touches files `main` changed ("Your
  local changes … would be overwritten by merge");
- a branch with commits whose rebase conflicts, which it aborts.

Ship's Step 0 then stops by rule ("Never resolve a conflict, stash, or retry it by hand from this
skill"), and the person is asked how to proceed: commit to the branch first, merge, or something
else. They answer "implement the approach", and the agent does it outside ship. It saves the diff
as a patch, restores the files, fast-forwards with `sdlc.py base`, reapplies with `git apply -3`,
merges each conflicting hunk keeping both sides' meaning, reruns the gate, and only then runs
`/sdlc:ship` again.

It happened twice on 2026-11-17. 071 conflicted with 070 on `README.md`. 074 conflicted with 072
on `.sdlc/work/inbox.md`, the factory's README, `factory.py`, the build skill and
`tests/test_factory.py`. In both, the person made no decision beyond "go ahead". The stop costs a
round trip and a second ship run, and the routine is reconstructed from memory each time. It grows
more frequent as the factory and parallel worktrees land changes faster.

## Outcome

- When `base` can't bring a change up to date because of a conflict, `/sdlc:ship` resolves it
  within the same run and goes on to the gate and review. It no longer stops and asks how. This
  covers both shapes: uncommitted work over files `main` changed, and a rebase of the branch's own
  commits.
- The mechanical half is the script's: setting the work aside without a stash, fast-forwarding or
  rebasing, reapplying, and listing the conflicted files and hunks. The judgment half is the
  agent's: merging each hunk so both sides' intent survives.
- Every resolution is visible at the gate. Ship's WAIT question and report name the files resolved
  and how. The review reads the resolved hunks as part of the diff, and `findings.md` records that
  a resolution happened.
- What can't be resolved safely still stops, with the work intact: conflict markers left, a
  resolution the gate fails, or a case the script can't classify. The person's uncommitted work is
  never lost. An undo line points back to where it started, as `base`'s `undo` does today.
- A test reproduces each shape (the 071 and 074 shapes): a fixture repo where `main` moves under
  uncommitted work and under committed work, with the script's steps run end to end.
- **Moves O3:** a change whose base moved during its build no longer stops its person outside
  ship's own WAIT, so the stops per change don't rise as more changes land in parallel.

## Affected

- **Area:** the core plugin's ship path.
- **Files & components:** `scripts/sdlc.py` (`cmd_base()`, and whatever new subcommand or mode does
  the set-aside, reapply and conflict listing), `skills/ship/SKILL.md` (Step 0's `refused` rule,
  and possibly a side file such as `skills/ship/conflict.md` read only when `preflight`'s
  `branches` names it), `ship_question()` (the WAIT clause naming a resolution), the findings note,
  `tests/`.
- **Downstream:**
  - Every host's ship runs. The WAIT question changes for a change that met a conflict.
  - The factory's landing (072's `cmd_land()` and `cmd_resolve()`) handles its own conflicts. The
    spec decides whether the two share a mechanism. `factory.py` can't import `sdlc.py`, but it
    already calls it through `_sdlc()`.
- **Contracts:**
  - *Always Tier 2*: a skill's WAIT step, what it approves or when.
  - `cmd_base()`'s rules: never a stash (the stack is shared across worktrees), never a merge of
    the base into the branch (close walks the first-parent line), and only the change's own branch
    moves.
  - `git.base` is never a literal `main` in a git call (`test_no_git_call_names_main_itself`).
  - Every command ship runs needs its own `Bash(...)` rule, and the logic stays in the script, not
    in bash.

## Constraints

- No uncommitted work is ever lost or silently rewritten (O2): a failed resolution leaves the
  worktree as it was, or says exactly how to get back.
- Never `git stash`, never a merge of the base into the branch, never a forced or destructive git
  flag.
- The resolution happens before the gate and the review, never after, so ship still commits only
  what its review read and its WAIT approved.
- Only the change's own worktree and branch are touched, never `main` or another worktree.
- The rule that a refused `base` stops ship still holds for anything that isn't a conflict, such as
  a rebase failing for another reason or a dirty tree in an unexpected state.

## Open questions

- ~~Should a resolution add a clause to ship's WAIT question, or is the findings note enough?~~
  Resolved: a clause. `ship_question()` reads the script-written `conflicts.md` itself (spec R9),
  so ship can't leave it out.
- ~~How does the script set uncommitted work aside without a stash: a patch file, or a temporary
  commit?~~ Resolved: a temporary commit kept under `refs/sdlc/aside/<branch>` until close, so a
  run that dies halfway leaves the work in a reachable commit (R2, R6).
- ~~Is a resolved conflict a risk signal that deepens the review?~~ Resolved: no fresh reviewer.
  Ship's gate is always the person's, the WAIT names the resolution, and the correctness pass reads
  each resolved file against both sides (R9, R10).
- ~~Does this share a mechanism with the factory's `resolve`?~~ Resolved: not now. 072's landing
  reads `base`'s refusal, which stays as it is (R1); a seed can revisit it if the two drift.
- ~~Should `.sdlc/work/inbox.md` conflicts be settled by the script alone?~~ Resolved: no, the
  agent merges them under `conflict.md`'s rule (R8). Only `.sdlc/last-id` is the script's (R5).
