---
id: 080
slug: board-tracks-manual-changes
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
reworks: [075]
serves: [O3]
---

# 080 — The board follows a change built by hand, through to close

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Watching the board (`/sdlc:dashboard`, `scripts/board.py`) while 079 was built by hand on
2026-11-17, its card never said where the change was:

- **It never left Plan.** `column()` (`scripts/board.py:244-251`) files a card by its `stage:` line
  alone, and on a change built by hand nothing moves that line between `plan` and `shipped`: plan
  mode, the build, ship's gate and review all leave it, and `sdlc.py ship` writes `shipped`
  directly. Only the factory walks `design`, `build`, `test`. So 079 sat in Plan through its build,
  its gate, its fresh review and its ship question.
- **It vanished once shipped.** `state()` drops every change whose stage is in
  `CLOSED = ("shipped", "dropped")` (`:32`, `:59`), but a shipped change isn't done until
  `/sdlc:close` lands it, and `/sdlc:status` lists it under Ready to close. The board showed nothing
  just when 079 was waiting on the person again. A dropped change awaiting close is hidden the same
  way.

The board is there to show at a glance which change waits on the person (075); for every change
built by hand, most of this repo's, it shows that wrong.

## Outcome

- **Moves O3:** a person running changes by hand sees from the board, not from asking
  `/sdlc:status`, which change waits on them and for what.
- A change built by hand at `stage: plan` moves from Plan to Build once its branch has commits
  beyond `main`'s or its worktree has edits outside its own folder, and to Test once its
  `findings.md` exists (ship's review has run). `tests/test_board.py` pins each step.
- A shipped or dropped change not yet closed stays on the board until close removes its worktree,
  in a column of its own (Ready to close) or under Needs you, its next step `/sdlc:close NNN`,
  pinned by `test_board.py`.
- A factory change's columns are as today: its stage line already moves, and its own signals
  (`decision.md`, a pending decision) still win.
- `./check.sh` passes.

## Affected

- **Area:** the board.
- **Files & components:** `scripts/board.py` (`state()`, `column()`, `next_action()`),
  `scripts/board.html` (`COLUMNS`), `tests/test_board.py`.
- **Downstream:** the person looking at the board; nothing else reads `/state.json`.
  `.sdlc/factory.toml`'s `[ui]` names these paths, so a factory run on this change would get the UI
  and UX reviewers. `sdlc.py status` and `check` are unchanged.
- **Contracts:** AGENTS.md's *The board*: it writes nothing, answers only GETs on `127.0.0.1`,
  builds every node with `textContent`, and reads with `status`'s own readers. *The scripts run on
  Windows*: git output compared as paths is `as_posix()`.

## Constraints

- The board still writes nothing, `stage:` included. The other fix, `sdlc.py` stamping `build` and
  `test` as a change moves, changes what `stage:` means for every host and is out of scope.
- What the board infers comes from what `status` already reads (`behind_trunk()`,
  `last_touched()`, `_dirty_paths()`, `findings_entries()`), not a second account of a change's
  progress.
- `/file` still serves only an open change's own folder; a shipped change not yet closed counts as
  open there too, since its folder is still on disk.

## Open questions

- ~~Ready to close: a column of its own, or a card under Needs you? It waits on the person, but it
  isn't a problem.~~ Resolved: a column of its own, after Ready to ship; Needs you stays for a
  decision or a problem.
- ~~Does a Tier 2 change built by hand at `stage: build` (set by hand after plan mode) move to Test
  on `findings.md` the same way, and does Design ever fill for one built by hand?~~ Resolved: yes,
  from `design` or `build`; Design fills from the stage line `/sdlc:spec` writes. A Tier 2 at
  `plan` stays there whatever it touches: it has no spec yet.
- ~~Commits on the branch beyond `main`'s: always the build? A change whose only commit is a `wip`
  of its intent would read as building.~~ Resolved: only paths outside `.sdlc/work/` and the
  plugin's state files (`.sdlc/last-id`) count, so an intent's `wip` and the register's
  `[building]` tag don't.

## Approach

In `board.py`, give `column()` a manual-only step: from `plan` (Tier 1), `design` or `build`, the
furthest stage the change's signals reach, leaving a factory change to its own. In `state()`, keep
a shipped or dropped change while its worktree or folder is still open, with a `close` column and
`/sdlc:close NNN` from `next_action()`. Add the column to `COLUMNS` in `board.html`. Pin each case in
`tests/test_board.py`, with fixture repos as the existing ones build them.
