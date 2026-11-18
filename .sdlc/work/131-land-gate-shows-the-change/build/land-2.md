## Report: conflict resolution, `plugins/factory/scripts/factory.py`

I resolved the one conflict, but the gate is still red: one test fails on a file outside the resolution. The landing's behaviour review, `.sdlc/work/131-land-gate-shows-the-change/reviews/land-1/behaviour.md` line 42, quotes a home-directory path. `test_nothing_local.py::test_nothing_in_the_repo_is_forbidden` refuses any such path in the repo. I was told to edit only the conflicted file, so I left it alone. That line needs `<path-to-clone>` in place of the path, or the review needs writing again, before the gate can pass.

The conflict was in the `entry` dict in `cmd_land_check()`.

- **Kept from the base branch:** `land_parts()` now takes `(folder, pre, worktree, cfg)`, and that call is unchanged. Its new `nits` part is in every entry, and the question's new "its agents' nits filed as shown" clause is untouched.
- **Kept from this change:** each entry's `"intent": intent_parts(folder)` and the output's `shown`.
- **Added to `land_shown()`:** an `Agents' nits to file:` part listing each nit's `shown` line. The question now calls those nits "as shown", and this change's purpose is that everything the question calls shown is in the dialog. Without it, the dialog would leave out exactly what the base just added. Nothing changed in `land_question()`, `land_parts()` or what a yes approves.

**No test for the nits part yet:** the new nits part has no test, because the test file wasn't mine to edit this time. A quick script shows it rendering as `Agents' nits to file:` / `- [nit] Rename x (naming, small, low; a.py)`, and the land tests still pass (64). The land skill's description of `shown` doesn't mention nits yet either. Both belong to the next round.

- DECISION: [default] Show the agents' nits in the dialog's `shown`, like every other part the question calls "as shown"? Going ahead with them included. The test that pins it and the skill's one-line mention come next round.

## Evidence

$ grep -c "^<<<<<<<\|^=======$\|^>>>>>>>" plugins/factory/scripts/factory.py
0

$ uv run --group dev ruff check plugins/factory/scripts/factory.py; uv run --group dev ruff format --check plugins/factory/scripts/factory.py
All checks passed!
1 file already formatted
exit: 0

$ uv run --group dev python -c "…land_shown([an entry with one nit])…"
001-a — T
  Agents' nits to file:
  - [nit] Rename x (naming, small, low; a.py)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_land.py
64 passed in 14.90s
exit: 0

$ ./check.sh > /tmp/131-gate.log 2>&1; echo "exit: $?" >> /tmp/131-gate.log; grep -E "passed|failed|All checks|formatted|^exit" /tmp/131-gate.log
All checks passed!
255 files already formatted
1 failed, 2404 passed, 13 skipped in 81.56s (0:01:21)
exit: 1

$ uv run --group dev pytest -q tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden -vv
E         Left contains one more item: '.sdlc/work/131-land-gate-shows-the-change/reviews/land-1/behaviour.md:42: tail: `<path-to-clone>...
FAILED tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden - A...
1 failed in 0.39s
exit: 1
