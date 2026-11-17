---
id: 080
slug: board-tracks-manual-changes
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 080 — The board follows a change built by hand, through to close · plan

## Context

While 079 was built by hand, its card on the board stayed in Plan from intent to ship, then
disappeared at ship, though the change was still waiting on `/sdlc:close`. Both problems come from
the board reading one thing:
- `column()` (`scripts/board.py:244`) reads only `stage:`, which nothing moves on a change built by
  hand.
- `state()` (`:59`) drops every `shipped` or `dropped` change.

The fix is for the board to read the signals `status` already has. It still writes nothing, and
`stage:` keeps its meaning.

## Design (resolving the intent's open questions)

1. **Ready to close gets its own column**, `close`, labelled "Ready to close", with the who-text
   `/sdlc:close`. It sits after "Ready to ship" and before "Needs you". Needs you stays for "a
   decision or a problem": a shipped change isn't either.
2. **Which shipped or dropped changes stay** is decided by `sdlc.ready_to_close(root)`
   (`scripts/sdlc.py:3218`), status's own reader: a change worktree that is still standing, holding
   a shipped or dropped folder. Any other closed folder is still left off. Its next step is
   `/sdlc:close <id>`. Problems still win and send the card to Needs you.
3. **Progress inferred for a change built by hand**, `mode == "manual"` only, so factory columns
   are untouched. It applies at Tier 1 `plan`, or Tier 2 `design` or `build`. A Tier 2 at `plan` has
   no spec yet, so its column stays where it is. The card goes to the furthest column its signals
   reach, and never back:
   - **Test:** its `findings.md` exists, meaning ship's review has run at least once.
   - **Build:** the change touches a path outside `.sdlc/work/` other than `.sdlc/last-id`. That is
     either the branch's own commits (`git diff --name-only --no-renames refs/heads/<trunk>...refs/heads/<name>`
     from the main checkout) or, when the change has a worktree of its own (`checkout_of(folder)`
     isn't `main_root`), its dirty paths (`sdlc._dirty_paths`). Leaving out `.sdlc/work/` means a
     `wip` commit of the intent alone, or the register's `[building]` tag, doesn't count as a build
     (open question 3). In the main checkout, other people's edits are nobody's change, the same
     rule `last_touched()` (`scripts/sdlc.py:3255`) follows, so only commits count there.
   - Neither: the stage line as it stands.
4. `next_action()` reads the column the inference gives, so a Build card says "build it, then
   /sdlc:ship" and a Test card "/sdlc:ship". It adds a `close` case.

## Changes

- **`scripts/board.py`**
  - A `_on_board(root)` helper returns the folders to show: open ones, plus closed ones whose
    branch `ready_to_close()` names. `state()` and `file_at()` both use it, so `/file` serves a
    change waiting on close and still nothing else.
  - A `_seen(entry, folder, home, trunk)` helper returns the inferred stage, or None. `_entry()`
    stores it as `entry["seen"]`, showing what the board inferred apart from `stage:`, before
    `next_action()` and `column()` read it.
  - `column()` adds `close` for a shipped or dropped stage, and uses `seen` for a manual change.
    Each read is wrapped in `read()` like the others, so a git failure becomes a `problems` line,
    never a crash.
- **`scripts/board.html`**
  - Add `{ key: "close", label: "Ready to close", who: "/sdlc:close" }` to `COLUMNS`.
  - The grid goes from `repeat(6, …)` to `repeat(7, …)`.
  - `.col.close` gets the accent heading, like `.col.ready`.
- **`tests/test_board.py`**: a new fixture, extending `repo` with real `git worktree add`s under
  `.claude/worktrees/`. Every new test is marked `portable`, except where a worktree makes that
  impossible. The cases:
  - A Tier 1 at `plan` with a worktree and a commit to `src/a.py` → Build, next "build it, then
    /sdlc:ship".
  - The same with only dirty edits, uncommitted → Build.
  - One whose only commit is under `.sdlc/work/` → Plan.
  - One with `findings.md` → Test, next `/sdlc:ship`.
  - A shipped folder in a standing worktree → `close`, next `/sdlc:close 007`, and `/file` serves
    its `intent.md`.
  - The existing `005-old-thing`, shipped with no worktree, stays off the board.
  - A factory change at `build` with code commits keeps its own column.
  - The existing assertions stay as they are: 001 has no branch, so it stays in Plan.
- **`.sdlc/work/080-…/plan.md`**: this plan, saved once approved. Strike the intent's three open
  questions with the resolutions above.

## Verification

- Run `uv run --group dev pytest tests/test_board.py -q`, then `./check.sh`.
- Live check: run `sdlc.py board --port 5171` from this worktree and read `/state.json`. 080 should
  read `"seen": "build"` once its code commits exist, and 078 `"column": "plan"`, since it has only
  intent edits. Then check the page renders seven columns.
- Context pass at ship: AGENTS.md's *The board* paragraph probably gains a sentence on inferred
  progress and the close column.
