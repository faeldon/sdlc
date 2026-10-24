# 011 — A worktree setup's cd no longer moves the session · plan

## Context

Intent Step 5 runs a host's `commands.worktree_setup` through the Bash tool, whose shell keeps its
cwd. A `cd {worktree} && …` there moves the session into the worktree, so `EnterWorktree` is
refused or skipped, and close's `ExitWorktree` later fails with "No-op: there is no active
EnterWorktree session to exit" (three changes in one host). Fix: run the setup in a subshell,
and tell close and drop the no-op is expected for a change opened before the fix.

## Open questions, resolved

- Bash-block parser and `( … )`: moot. The setup command is described in prose in intent Step 5,
  never a fenced block (it's the host's command, so no `allowed-tools` rule can cover it), and it
  stays prose.
- README / REFERENCE: no update. REFERENCE's "run from the main checkout" (lines 33, 77) stays
  true, and a host needn't know a `cd` is now harmless.

## Changes

1. `skills/intent/SKILL.md` Step 5: "run it from the **main checkout** next, with `{worktree}`
   replaced by that path" becomes "run it from the **main checkout** next, in a subshell,
   `(<command>)`, with `{worktree}` replaced by that path", plus a sentence on why: a `cd` in it
   would move this session into the worktree before `EnterWorktree` does.
2. `skills/close/SKILL.md` Step 3.1: append "If it answers `No-op: there is no active EnterWorktree
   session`, the session came in by `cd` or started there: go on to 2, where exit 3 is that case."
   No new command, so `allowed-tools` is unchanged.
3. `skills/drop/SKILL.md` step 3: the same sentence, pointing at 4.
4. `tests/test_skills.py::test_intent_moves_the_session_and_close_brings_it_back`: add
   - intent's Step 5 has `subshell, `(<command>)``, and `worktree_setup` comes before
     `EnterWorktree` in it;
   - close's and drop's content have `No-op: there is no active EnterWorktree session`.
5. Intent's `## Open questions`: strike both as resolved above.

## Verification

- `uv run --group dev pytest tests/test_skills.py -q`, then `./check.sh` (the full gate).
- `git status --short`: only the four files and the change folder.
- Manual (not run here, no host with a setup in reach): the next host intent with a `cd`
  setup gets a successful `EnterWorktree`, and its close a successful `ExitWorktree`.

## Rollback

`git revert <sha>`: prose and a test only, nothing a host stores.
