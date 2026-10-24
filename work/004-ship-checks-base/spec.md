---
id: 004
slug: ship-checks-base
kind: spec
created: 2026-10-24
updated: 2026-10-24
---

# 004 — Catch a stale base at ship, not at close · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. `behind_main(main, branch)` counts `main`'s commits that `branch` lacks: 0 when `main` is an
   ancestor, N after `main` gains N, None when either branch doesn't exist. Tested.
2. `sdlc.py status` marks an open change whose branch is behind with
   `· behind main by N: /sdlc:ship brings it up to date`, and a shipped one under **Ready to
   close** with `(behind main by N: rebase and ship again)`; `check --strict` never reports
   either. Tested.
3. A new `sdlc.py base <NNN>` brings the change's branch up to date with `main` in the change's
   own worktree, or refuses, printing JSON: `change`, `branch`, `behind`, `action` (`current`,
   `fast-forwarded`, `rebased` or `refused`), `from` and `to` (shas), `undo` (the command that
   reverses it) and `reason`. It exits 1 only on `refused`.
4. **No commits of its own** (the usual case at ship, and always after a factory build): `base`
   fast-forwards the branch to `main`, carrying uncommitted edits unchanged. When git refuses
   because `main` touched a file the uncommitted work did, `base` refuses with HEAD and every file
   as they were. Tested: edits carried byte for byte; an overlapping file refused.
5. **Commits of its own, clean tree:** `base` rebases onto `main`; on a conflict it runs
   `git rebase --abort` and refuses, HEAD where it was. Tested: a clean rebase and a conflicting
   one.
6. **Commits of its own and uncommitted work:** `base` refuses and runs nothing, saying to commit
   the work and run ship again. Tested.
7. **The local counter doesn't block it.** An untracked `.sdlc/last-id` in the worktree, when
   `main` has a committed one (another change closed under local numbering), is set aside for the
   fast-forward and afterwards holds the higher of the two numbers; on a failed fast-forward the
   original is put back exactly. Tested both ways.
8. `base` never forces, stashes, autostashes, fetches or pushes, and touches only the change's
   branch in its worktree: `main` and the main checkout are untouched. Tested: `main`'s sha and
   the main checkout's status before and after.
9. A **factory-built change** (uncommitted code, `decision.md`, `decisions.md`, `reviews/`)
   fast-forwards with all of it intact. Tested.
10. `/sdlc:ship` Step 0 runs `sdlc.py base <NNN>` after `status`, with no prompt, and reports what
    moved with the undo command; on `refused` it stops before Step 1 with the reason. Ship gains
    one `allowed-tools` rule and keeps exactly one WAIT; `tests/test_skills.py` passes.
11. Close's fast-forward refusal uses `behind_main()`, its text and behaviour unchanged; the
    existing diverged-branch test passes.
12. `docs/REFERENCE.md`, `.sdlc/SDLC.md` and `defaults/SDLC.md` (the same edit in both) say ship
    brings a stale base up to date and stops when it can't.

## Design

`behind_main()` and the status mark exist already. The new piece is `cmd_base(root, ident)`,
which finds the change's worktree through `worktrees(root)` and `names_change()`, as
`cmd_close()` does. Outside a change worktree (a change in the main checkout), it reports
`current` with that reason and does nothing.

It decides in order:

1. Behind 0 → `current`.
2. Commits of its own (`rev-list --count main..branch`): with a dirty tree → `refused`; with a
   clean one → `git rebase -q main`, and on failure `git rebase --abort` → `refused`.
3. No commits of its own → `git merge --ff-only -q main` in the worktree. Git refuses by itself
   rather than overwrite local changes; `base` passes that refusal through.

The counter: before the fast-forward, if `.sdlc/last-id` is untracked in the worktree and exists
in `main`'s tree, `base` reads it (`read_last_id()`) and removes it; after success it writes the
higher number back, so the bump still lands with the change; on failure it writes the original
back.

`undo` is `git reset --keep <from>` either way: run in the worktree, it puts the branch back and
keeps uncommitted work. All branching lives in the script, so ship's bash stays one plain
command. `base` is not in `READ_ONLY`: it writes, so setup never proposes allowing it outside
ship.

## Contracts touched

- **Confirm before writing (`.sdlc/REVIEW.md`, Pass 2): a named exception, approved 2026-10-24.**
  `base` writes before ship's WAIT, without asking, because it only moves the change's own local
  branch onto `main`, only when nothing conflicts, prints the one command that reverses it, and
  ship reports it. Anything not clean is a refusal that touches nothing. This exception is this
  one, not a general one.
- **Exactly one WAIT** (`tests/test_skills.py`): unchanged; ship adds none.
- **Narrow `allowed-tools`:** one rule,
  `Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py base *)`; no
  `git rebase` or `git merge` rule, and no `if` in bash, since the logic is in `sdlc.py`.
- **Only publish pushes:** `base` neither fetches nor pushes; `"push"` doesn't appear in it.
- **Close refuses rather than forces:** unchanged; close still only fast-forwards, and still
  refuses when `main` moved after ship.
- **Numbering:** the counter only ever keeps the higher number, never lowers it, so no number is
  handed out twice.
- **Mechanism vs. policy:** `main` is the base, as in `cmd_close()`; no new config key.

## Alternatives rejected

- **Merging `main` into the branch.** Close's fast-forward would put the branch's merge commit on
  `main`'s first-parent line, and `closed_changes()` would walk the branch's side, skipping the
  `Close` commits that landed in between: release and retro would miss changes.
- **Autostash, or stashing around a rebase.** The stash stack is shared across worktrees and
  sessions, and re-applying a stash can conflict after the branch has moved.
- **Asking before updating.** One more stop every time `main` moved, against O3; the person chose
  against it.
- **Rebasing in close.** Close has no gate and no review: code would land untested.
- **Updating the base before the factory's review rounds.** `factory.py` can't share `sdlc.py`'s
  code, and ship's step covers factory-built changes; deferred.
- **Comparing against a remote `main`.** Close merges into the local one, and only publish talks
  to the remote.

## Verification

- `uv run --group dev pytest tests/test_sdlc.py -q -k "behind or base or stale or close or
  status"`: every requirement's test passes.
- `uv run --group dev pytest tests/test_skills.py -q`: ship's new rule is used and it keeps one
  WAIT.
- `./check.sh` exits 0.
- In a scratch repo (the tests): a change opened, a commit on `main`, `sdlc.py base` prints
  `fast-forwarded` with `behind: 1`; run again, `current`.
