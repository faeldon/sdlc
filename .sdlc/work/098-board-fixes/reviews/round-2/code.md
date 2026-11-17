VERDICT: PASS

## Notes

Round 2 items:

- **Reload text (`scripts/board.py`, `_Live.current()`):** done. The message now reads "`board.py` changed but won't load (…): the board serves the code it had until the file loads", with no restart. The header shows it as `stale · …` through `textContent`, and the test asserts "restart" is absent.
- **Problems before close (`next_action()`):** done. A card with `problems` at any stage now reads "fix what its problems name". `test_a_card_with_a_problem_never_names_close` covers shipped, dropped, build, test and plan. Only a missing stage (frontmatter fix) returns earlier, which is correct.
- **Rebasing card (`next_action()`):** done. The card says the rebase is stopped and names `sdlc.py resolve <id> --continue` or `--abort`. Those are the forms `skills/ship/conflict.md` uses, and the flags exist in `cmd_resolve`'s argparse. The rebasing check runs before the problems check, which is what the plan asks for.

New points, none required:

- **`next_action()` for a card with a problem and a pending decision at build.** Before this change, the card read "answer its decision in the factory's supervisor". Now it reads only "fix what its problems name", so the card no longer tells the person the decision is waiting on them. The decision is still listed on the card, so nothing is lost. Consider "fix what its problems name, then answer its decision in the factory's supervisor". This is a judgement call the plan already accepts.
- **The `--abort` line.** It says "resolve, or abort", without saying that abort puts the worktree back and keeps the resolved work under `refs/sdlc/end/<branch>` (per `cmd_resolve`'s docstring). A person may fear losing work. Saying "the work is kept" would help. Optional.

What is done well:
- The problems branch is placed before the close branch, so a card with a problem can't name a close, and the test covers each stage.
- The rebasing line uses the command the skills already name, in the same `<id>` form.
- The rebase's card keeps its place, and `test_a_change_being_rebased_keeps_its_card` checks that reading it leaves git's status, HEAD and branch unchanged.

What I ran:
- I did not run the tests. `python3 -m pytest` on the system interpreter has no pytest, and `uv run` would create a `.venv` in the worktree, which this review must not write. The findings above come from reading the code, the diff and the tests.
