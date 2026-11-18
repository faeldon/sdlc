VERDICT: PASS

I ran the end-to-end path through the tests that build a train to a conflict with a stand-in `claude`. The factory, train, resolve, skills, land and board test files passed: 1127 passed, 28 skipped. I did not run a real landing with a live model.

## Notes
- **`checks.md`, "The docs say the builder and the resolver edit, and the builder no longer resolves":** I read the section and ran no `sdlc.py accept`. I expect it to pass. I ran its grep conditions one by one, copying the strings from the section, and each returned 0. The old phrases are gone, `builder.md` has no "A conflict, while landing" section, AGENTS.md and the factory README carry the new rule, and the README has the `resolver` table row.
- **`train-resolve` runs the resolver:** `TASK_ROLE` maps it to `resolver`, and `ROLES` and `FIXED_MODELS` give it sonnet. `RESOLVE_RECORDS` now includes `runs/resolver.sessions`.
- **Wrong `--role`:** `cmd_agent` refuses a role other than `resolver` for `train-resolve`.
- **Files outside the conflict:** `_stray()` makes `resolve --continue` refuse a resolution that changed anything outside the conflicted files and the change's landing records.
- **Not run:** a landing against a live model.

## Evidence
$ cd <worktree> && git diff e7bb2a3a452aa654e3dbc4ac13abbe23009d749c...HEAD --stat | tail -3
 tests/test_train.py | 135 ++++++++--
 57 files changed, 1887 insertions(+), 98 deletions(-)
exit: 0

$ cat .sdlc/work/149-landing-resolver-agent/checks.md; git diff e7bb2a3a452aa654e3dbc4ac13abbe23009d749c...HEAD -- plugins/factory/scripts/factory.py
(the checks.md section and the factory.py diff, read in full)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_train.py tests/test_resolve.py tests/test_factory.py tests/test_skills.py tests/test_land.py tests/test_board.py
1127 passed, 28 skipped in 164.56s (0:02:44)
exit: 0

$ ! grep -rnE "landing agent, the builder|Only the builder edits" plugins AGENTS.md; echo a=$?
a=0
exit: 0

$ ! grep -q "## A conflict, while landing" plugins/factory/agents/builder.md; echo b=$?
b=0
exit: 0

$ grep -q "only the builder and the resolver edit" AGENTS.md; echo c=$?
c=0
exit: 0

$ grep -q "Only the builder and the resolver edit" plugins/factory/README.md; echo d=$?
d=0
exit: 0

$ grep -q '^| `resolver` |' plugins/factory/README.md; echo e=$?
e=0
exit: 0
