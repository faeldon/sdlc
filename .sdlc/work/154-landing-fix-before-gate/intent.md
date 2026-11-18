---
id: 154
slug: landing-fix-before-gate
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on: [147]
serves: [O3]
---

# 154 — A landing's fix is applied before the gate that needs it

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A landing's `yes, with a fix` is applied too late: in a train the fix runs at the change's close,
after the tip gate, so a fix meant to make that gate green never runs. Seen 2026-11-18 landing 147
alone: its fix (stage `runs/land-times.jsonl` in `RESOLVE_RECORDS`) was what the gate needed, the
gate went red on `test_a_resolution_leaves_the_worktree_clean`, and the train ejected 147 before
the fix step; the fix was then made by hand through `/sdlc:ship`, with a second commit. The land
skill places the fix "here, before its close", and the train's reading names `fix` only once the
change's landing round has passed, so a fix the person asked for is approved and then silently
skipped whenever the gate is what it fixes.

## Outcome

- With `yes, with a fix`, the train's reading names the fix step for that change as soon as it is
  stacked (or committed, for a change that didn't move), before the first gate, so the tip gate and
  the landing review read the fixed change.
- A test lands a change whose gate fails until the fix is made, with `yes, with a fix`, and finds
  the fix applied, the gate green and the change landed, never ejected.
- The land skill says where the fix comes, and 147's `train --run` loop takes the same order.
- **Moves O3:** a fix the person asked for at landing is the one that gets gated and reviewed, so a
  landing doesn't stop over a problem the person already answered.

## Affected

`plugins/factory/scripts/factory.py` (`cmd_train()`'s reading of where `fix` falls,
`cmd_land_fix()`, 147's `train --run` steps), `plugins/factory/skills/land/SKILL.md` (where the
fix comes), `tests/test_train.py` and `tests/test_land.py`. Every factory host's landings with a
fix. It waits on 147, which rewrites the train's steps, and lands before 153 moves the landing
code.

## Constraints

- A fix stays the person's words, once per landing, made by the change's own builder and amended
  into its commit.
- A fix made while landing is still a signal: every reviewer at the run's depth reads it, and it
  never lets a later landing pass by itself.
- The re-stack of the changes above it and the re-gate of the tip are unchanged.

## Open questions

- For a change that conflicts when stacked, does the fix come after the resolution, or before the
  stack?
- Is the person's fix ever meant for after the gate (a fix to something only the landing review
  would raise), so the person should be able to say which?

## Approach

In `cmd_train()`'s reading, when the train holds a fix for a change and its fix round hasn't run,
name `fix` for that change right after `stack` (or `commit` when it didn't move), before `gate`;
drop the before-close placement. The land skill's `close` bullet moves to say the fix comes before
the gate, and 147's `RUN_STEPS` with it. A test in `tests/test_train.py`: a stand-in builder whose
fix is what makes the gate green, landed.
