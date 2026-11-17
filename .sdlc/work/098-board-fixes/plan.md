---
id: 098
slug: board-fixes
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 098 — The board shows a change as it is · plan

> A Tier 1 whose Approach reaches past a couple of files, so planned after reading the code:
> what changes, in what order, and which test proves each outcome.

## Files to change

- `scripts/sdlc.py`: `change_dirs()` walks `_change_trees()` instead of `worktrees()`, so a change
  worktree stopped mid-rebase (detached, its branch in `rebase-merge/head-name` or
  `rebase-apply/head-name`) still yields its folder. Reuses `_change_trees()` and
  `_rebase_branch()`, which `resolve` already reads with (`git rev-parse --git-path`, read-only).
  `worktrees()` itself is unchanged, so `base`, `close`, `resolve` and the numbering keep reading
  only checkouts with a branch out.
- `scripts/board.py`:
  - `state()` marks each card `rebasing` (branches `_change_trees()` finds that `worktrees()`
    doesn't); `_entry()` takes it as a keyword.
  - `next_action()` names the first state a card holds, in one precedence (below), so a card
    in two states names the higher one's step: a stopped rebase before anything, a card's
    `problems` at any stage before close or the stage's own step.
  - `_progress()` takes `decision.md` as a finished run only at `test`, `shipped` or `dropped`,
    the stages `column()` already reads it at (086).
  - Reload: routing moves into a module function `route(root, path, notice)`; the handler (kept
    by the first module, with its Host check) asks a `_Live` holder for the `route()` to answer
    with. The holder compares `board.py`'s `st_mtime_ns` on each request and loads the file afresh
    by path (`_load()`, binding the same `sdlc`); a load that raises, or a module with no
    `route()`, keeps the last that loaded, and `state.json` carries `reload_error` saying so.
  - `cmd_board()` prints the URL from `server.server_address[1]`.
- `scripts/board.html`: a `rebasing` badge, and the `reload_error` shown in the header's status,
  both through `h()`/`textContent`.
- `docs/REFERENCE.md`, *The board*: the rebasing badge and the reload, one sentence each.
- `tests/test_board.py`: the tests below; `test_a_decision_or_a_stop_overrides_the_record` now
  sets `stage: test` for the decision half, since at `build` a decision no longer counts.

## The precedence of `next_action()`

Highest first; a card names the step of the first state it holds. Rounds 1 and 2 each reordered
one pair and left another wrong (problems after close, rebasing after the stage's step, then
rebasing after a missing stage), so the whole order is stated here once and pinned pair by pair.

| # | State | Fields | Its step |
|---|---|---|---|
| 1 | rebasing | `rebasing` | `sdlc.py resolve NNN --continue`, or `--abort` |
| 2 | stage missing | `problems`, no `stage` | fix intent.md's frontmatter |
| 3 | problems | `problems` | fix what its problems name |
| 4 | closed | `stage` shipped or dropped | `/sdlc:close NNN` |
| 5 | stopped | `stopped` | the stop's own `next` |
| 6 | decision pending | `pending` at `build` | answer its decision in the factory's supervisor |
| 7 | approver decided | `decision` at `test` | `/sdlc:ship`, or `/sdlc-factory:land` |
| 8 | factory building | factory, `built`, at `design` or `build` | wait for its decision |
| 9 | red gate | `gate` current and FAIL | read build/gate.md, fix it, `sdlc.py gate NNN` |
| 10 | its stage's step | — | `/sdlc:spec`, plan mode, build it, or `/sdlc:ship` |

Why this order: a rebase stopped mid-way makes every other step moot, and its conflicted files
may be why `intent.md` won't read. A problem is the card's column at any stage (`column()`), so
it is its step too, over close (a shipped change whose files won't read isn't ready to close)
and over a factory signal (a pending decision at `build` under a problem reads only the problem;
answering it waits until the files read). The rest is the order `next_action()` already had.

## Work order

1. **Close after problems**: test, then the `next_action()` reorder. Round 3: the precedence
   table's test, every pair, then rebasing moved above the missing stage, the one pair it failed.
2. **Decision only at its stage**: test (a change at `build` with a `decision.md` shows its
   record's track; at `test`, all done), then `_progress()`.
3. **Port 0**: test (`serve_forever` patched to raise `KeyboardInterrupt`), then `cmd_board()`.
4. **Rebasing**: test (a worktree's rebase stopped on a conflict; the card is there, `rebasing`
   true, and git's state unchanged by reading), then `change_dirs()`, `state()`, the page badge.
5. **Reload**: test (a copy of `board.py` and `board.html` in a temp dir, served; the copy edited
   to add a key to `state()`, then broken), then `_Live`, `route()`, `_load()`, the page's line.

## Tests

- `test_a_card_with_a_problem_never_names_close`: outcome 2 (2026-11-17-23), on real folders.
- `test_a_card_in_two_states_names_the_higher_ones_step`: the precedence table above, as
  `PRECEDENCE`; every pair of states that can overlap (two that set different stages can't) names
  the higher one's step, by its full text, "fix what its problems name" included.
- `test_a_decision_counts_on_the_track_only_at_its_stage`: outcome 4 (nit 2026-11-17-22).
- `test_board_on_port_0_prints_the_port_it_bound`: outcome 5.
- `test_a_change_being_rebased_keeps_its_card`: outcome 1 (2026-11-17-30), and that reading it
  leaves `git status` and the rebase as they were.
- `test_the_running_board_serves_board_py_as_it_is_on_disk`: outcome 3 (2026-11-17-47), and the
  constraint that a module that won't load keeps the old one and says so.
- `test_the_rebasing_badge_is_built_as_text` and `test_a_board_that_wont_reload_says_so_on_the_page`:
  the page shows both, through `h()`.
- `test_status_never_loads_the_board` is extended only if the reload adds a load call in
  `sdlc.py` (it doesn't: the reload loads by path inside `board.py`).

## Rollback

Nothing is written outside the code: `git revert` undoes it all. A running board started on this
code keeps reloading `board.py` until it is restarted.
