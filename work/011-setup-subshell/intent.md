---
id: 011
slug: setup-subshell
tier: 1
impact: patch
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea:
depends_on:
serves: none
---

# 011 — A worktree setup's cd no longer moves the session

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:intent` Step 5 runs the host's `commands.worktree_setup` through the Bash tool, whose shell
keeps its working directory between calls. A host with `worktree_setup = "cd {worktree} && uv sync
--quiet --extra test --locked"` leaves that shell inside the new worktree, and Claude Code moves
the session there by itself ("Environment update: Primary working directory:
…/.claude/worktrees/NNN-…").

The step's next instruction, `EnterWorktree`, then fails or is skipped. In one change it was
refused: "Cannot enter worktree: … is the current working directory". In two others the model saw
the session was already there and didn't call it.

So no session ever had a successful `EnterWorktree`. At `/sdlc:close` Step 3, `ExitWorktree` then
fails with "No-op: there is no active EnterWorktree session to exit", twice per close, before the
model `cd`'d back to the main checkout by hand. The close still worked, but every change in that
host ends with a tool error and a workaround, and the person asked whether their config was wrong.

## Outcome

- Intent Step 5 runs `worktree_setup` from the main checkout in a subshell, `(<command>)`, so a
  `cd` in it is gone when it exits. `EnterWorktree` then succeeds, and close's `ExitWorktree` has
  a session to exit.
- Close Step 3, and drop's matching step, say that a "No-op: there is no active EnterWorktree
  session" reply means the session came in by `cd`. It is not a failure: carry on to the
  `sdlc.py close` step, whose exit 3 already covers a session inside the worktree. This covers
  changes opened before this fix.
- A test in `tests/test_skills.py` fails if intent stops running the setup command in a subshell.

## Affected

- **Area:** the skills.
- **Files & components:** `skills/intent/SKILL.md` Step 5, `skills/close/SKILL.md` Step 3,
  `skills/drop/SKILL.md` step 3, `tests/test_skills.py`.
- **Downstream:** every host with a `commands.worktree_setup`. Its command still runs from the
  main checkout with `{worktree}` substituted, so nothing they wrote changes meaning.
- **Contracts:** `docs/REFERENCE.md`'s "run from the main checkout" holds. No WAIT or
  `allowed-tools` change: the host's command was never covered by a rule and still isn't.

## Constraints

- Hosts' existing `worktree_setup` values keep working unchanged, including ones without `cd`.
- No `if` or other logic in a bash block. A subshell is plain bash; check whether the bash-block
  rule test accepts the parentheses.

## Open questions

- ~~Does `tests/test_skills.py`'s bash-block parser accept a `( … )` example, or should the
  subshell be described in prose instead of a fenced block?~~ Resolved: moot. Step 5 describes
  the host's command in prose, never a fenced block, since no rule could cover it; it stays prose.
- ~~Should README or REFERENCE tell hosts that a `cd` in `worktree_setup` is now harmless, or leave
  it unsaid?~~ Resolved: unsaid. REFERENCE's "run from the main checkout" stays true.

## Approach

In intent Step 5, change "run it from the **main checkout** next" to run it from the main checkout
in a subshell, `(<command>)`, so a `cd` in it can't move the session. Add one sentence to close
Step 3.1 and drop's matching step treating the `ExitWorktree` no-op as expected for a session that
came in by `cd`. Add an assertion to `tests/test_skills.py` that the intent skill names the
subshell.
