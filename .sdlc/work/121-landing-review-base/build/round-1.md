I built 121, and the gate passes (2249 tests passed, 13 skipped). Nothing is committed.

**The fix.** A landing review now reads the change's diff from the commit its round was rebased onto, not from the base branch's current tip. Before, the reviewers were told to review "its whole diff against `<base>` as it now stands". A commit that reached the base during the landing then looked like something the change deleted, which is what stopped 110's and 116's landings.

**Slice built (one):**
- **Prompts.** A new `_land_diff()` in `factory.py` gives both the `land-review` and `land-verify` prompts `` `git diff <fork>...HEAD` ``, where `<fork>` is `git merge-base <base> HEAD`. The prompt also says the base may have moved since, that a commit not in that diff isn't the change's, and that the script catches a move before the close, so it is never a finding. I updated the `_land_task()` docstring to match.
- **Agents.** `reviewer-code.md`, `reviewer-security.md`, `reviewer-test.md` and `verifier.md` each get one paragraph: a landing round's change is committed, so read the diff the prompt names, never one against the base branch as it is now. Their old wording ("`git diff`, uncommitted by design") only fits a build round. I left the behaviour, UI and UX reviewers alone because they don't read a diff.
- **Plan.** `plan.md` is written. The intent's Approach suggested recording the round's base; the plan instead reads it from git when the prompt is built, so nothing new is recorded.

**Test added.** `tests/test_land.py::test_a_landing_review_reads_the_change_from_its_rounds_own_base` rebases a change in a landing and then moves the base branch again. It checks four things:
- Both prompts name `git diff <the round's base>...HEAD` and never the moved tip.
- That diff holds the change's file and not the later commit's.
- The prompt says the base may have moved.
- `land-close` still reports `moved`, so a base that really moved still goes back through a round, as the intent's constraint requires.

Before the fix it failed because the prompt read "against main as it now stands".

**Notes.** Nothing was added to `notes.md`.

- DECISION: [default] Read the round's base from git when the prompt is built (`git merge-base <base> HEAD`), not from the gate record or a new record written by `land`. This answers the intent's open question. Within a round the base only moves forward from the rebase point, and the amend that adds the landing's record keeps `HEAD`'s parent, so the merge base is always the round's own base and nothing new has to be written or kept in step. Going ahead with this unless told otherwise.

## Evidence

$ uv run --group dev pytest -q tests/test_land.py -k rounds_own_base   (before the fix)
E           AssertionError: Change folder: .sdlc/work/001-mended. … Review landing round 1: the change was rebased onto main, with no conflict. Review its whole diff against main as it now stands.
FAILED tests/test_land.py::test_a_landing_review_reads_the_change_from_its_rounds_own_base
1 failed, 49 deselected in 7.34s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k rounds_own_base
1 passed, 49 deselected in 16.87s
exit: 0

$ ./check.sh
2249 passed, 13 skipped in 68.91s (0:01:08)
✔ Validation passed
✔ Validation passed
exit: 0
