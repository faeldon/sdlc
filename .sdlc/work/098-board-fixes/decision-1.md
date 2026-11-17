DECISION: ESCALATE

**Why.** Both rounds were used and one finding is still open. In round 2 the ux reviewer flagged that `next_action()` checks for a missing stage before it checks for a rebase. I read `scripts/board.py:601-605` and confirmed it. So a change whose `intent.md` is conflicted mid-rebase says "fix intent.md's frontmatter" and never says a rebase is stopped. That is exactly the case the comment at 603-604 is there for. The other two findings are the code-reviewer notes listed as non-blocking below. Everything else checks out: code and ui pass, the gate is green on the current build (`./check.sh`, 2005 passed), and all five outcomes have a test. But two decisions are still unticked defaults, and one of them, D2, changes what `change_dirs()`, and so `status`, see.

**Open items**
- ux (round 2, kept by the verifier): `scripts/board.py:601-605`: the rebasing check should come before the `problems and stage is None` return, so every rebasing card names `sdlc.py resolve NNN --continue / --abort`. It's already an unticked line in `notes.md`.
- code (round 2, note, not a CHANGE): a card with a problem and a pending decision at `build` now reads only "fix what its problems name". It no longer says a decision is waiting.
- code (round 2, note): the `--abort` wording doesn't say the resolved work is kept under `refs/sdlc/end/<branch>`.
- `notes.md` also has 5 unticked pre-existing lines for ship to dispose of: the col-head wrap, the drawer focus trap, Needs you sitting low at 390px (filed twice, once in round 1 and again in round 2), and the bare "—" for an empty column.

**Decisions to confirm**
- D1: the default is to reload `board.py` when it changes on disk, keep the old module if a load fails, and say so on the page. The alternative was only marking the page stale.
- D2: the default is that `change_dirs()`, and so `status`, also see a change being rebased, through `_change_trees()`. `worktrees()` stays as it is, so `base`, `close`, `resolve` and numbering don't change. This reaches past the board.

**For the person at ship**
1. `next_action()` in `scripts/board.py` (about 597-630): the order of the checks is the whole open finding.
2. `change_dirs()` in `scripts/sdlc.py`: it now walks `_change_trees()`. Check that nothing that writes (`close`, `base`, numbering) reads through it. This is D2.
3. `_Live` / `_load()` / `route()` in `board.py`. The round-1 code note still stands: `_load()` goes through `spec.loader.exec_module`, which reads the `.pyc` cache. An edit of the same size in the same second can serve stale code, and a running board writes `__pycache__` into the plugin. Round 2 didn't raise it again, and the build report doesn't say it was changed.

## Reconsider the approach

The fixes landed. What came back each round was the **order of checks in `next_action()`**:
- Round 1: problems vs. close, and rebasing vs. the stage's own step.
- Round 2: missing stage vs. rebasing.

Each fix moved one check and left another pair in the wrong order. The approach and the intent are fine; they don't need to change. The plan should, plus the tests:
- `plan.md` described the new order only for the pairs a review had raised. It should state the full precedence once: rebasing, then missing stage, then problems, then closed, then stopped, and so on.
- A test should check each pair of states that can overlap. Today `test_a_card_with_a_problem_never_names_close` only checks that close isn't named. The ux reviewer noted that nothing pins the "fix what its problems name" text itself.

Another builder round on the code alone would probably find the next pair. What's needed is a one-line reorder plus that precedence table and its test, which a person can make at ship. If D2 is declined, `change_dirs()` goes back and the board reads rebasing worktrees on its own.

- IMPACT: patch — the board now shows a change as it is (rebasing cards stay, no close under a problem, the step track is right after a change is put back to build), reloads `board.py` from disk, and `--port 0` prints the real port; `status` also stops losing a change mid-rebase (D2). Nothing anyone receives needs doing differently.
