DECISION: READY

**Why.** In round 3 the code, ui and ux reviewers all returned `VERDICT: PASS`. The finding that kept the earlier run open is fixed: the rebasing check now runs before the missing-stage check in `next_action()`. The plan now states the full order of checks once, and a new test pins every pair of states that can overlap, by the full text each card names. All five intended outcomes have a test, and `./check.sh` passed on the current build (2051 passed, 9 skipped). Both decisions, D1 and D2, are ticked, and the build follows them. Everything still open is minor and is an unticked line in `notes.md`.

**Open items**
- code (round 3 note, optional): `_load()` uses `spec.loader.exec_module`, which reads and writes `__pycache__` in the plugin's `scripts/`. An edit of the same size within the same second could serve old code. Not in `notes.md`; this was also item 3 in `decision-1.md`.
- code (round 2 note, in `notes.md`): a card with a problem and a pending decision at `build` names only "fix what its problems name". The table orders it that way on purpose.
- code (round 2 note, in `notes.md`): the `--abort` wording doesn't say the resolved work is kept under `refs/sdlc/end/<branch>`.
- ux (round 3 note): the rebasing line's "resolve its conflicts" doesn't point to the conflicted files.
- ui (round 3 note): the rebasing next line is long for a 168px column. It wraps but reads like a paragraph.
- `notes.md` has five older, unrelated layout lines for ship to sort out: the column-header wrap, no focus trap in the drawer, Needs you sitting low at 390px (filed twice), and the bare "—" in an empty column.

**Decisions to confirm**
- None. D1 (reload `board.py` when it changes, keep the old module if a load fails) and D2 (`change_dirs()`, and so `status`, see a change mid-rebase through `_change_trees()`; `worktrees()` unchanged) are both decided by you, and the build follows them.

**For the person at ship**
1. `change_dirs()` in `scripts/sdlc.py`: it now walks `_change_trees()`. This is the one part that reaches past the board. Check that nothing that writes (`close`, `base`, numbering) reads through it. The code reviewer found it applies the same `DIR_RE` filter as before.
2. `_Live`, `_load()` and `route()` in `scripts/board.py`: the reload, and whether the stale-bytecode note is worth a `sys.dont_write_bytecode` before it lands.
3. `next_action()` (around `board.py:600-630`) against the precedence table in `plan.md`, and `PRECEDENCE` in `tests/test_board.py`.
4. The notes above: decide for each whether to carry it to the inbox or drop it, since `sdlc.py ship` refuses while one is unticked.

- IMPACT: patch — The board now shows a change as it is: a card stays during a rebase, a card with a problem no longer names close, and a change put back to build shows its steps undone. The board also reloads `board.py` from disk, `--port 0` prints the port it actually bound, and `status` no longer loses a change mid-rebase. Nobody holding the previous release has to do anything differently.
