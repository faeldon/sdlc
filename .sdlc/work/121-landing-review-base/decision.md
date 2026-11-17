DECISION: ESCALATE

**Why.** The build does what the intent asks. Landing reviewers and the verifier now read `git diff <merge-base>...HEAD`. With no fork point, both landing tasks refuse with `_NO_FORK` instead of falling back to the base branch's tip. Round 2 is `VERDICT: PASS` and the gate passes (2250 passed). But two decisions in `decisions.md` are still unticked, and the build depends on them: it works out the round's base from git when it builds the prompt. Both the intent's Approach ("Record the base each landing round was rebased onto") and its open question pointed at recording that base instead. You need to confirm the departure before this lands.

**Open items.** None. code C1 (round 1, the silent `or base` fallback to the moved tip) was fixed in round 2, and the code reviewer confirmed the fix. Three round-1 nits were never filed as items and are still in the code:
- code (nit): `factory.py:2000`: the `LAND_TASKS` comment still says "the review of the change as it now stands on the base branch". That is no longer true.
- code (nit): `_land_diff()`'s docstring says "a later move of the branch". It means the base branch, so it should say so.
- code (nit, round 2): `_land_diff()`'s docstring is longer than it needs to be.

**Decisions to confirm.**
- D1: the round's base is read from git when the prompt is built (`git merge-base <base> HEAD`), not from the gate record or a new record written by `land`. This answers the intent's open question.
- D2: the code reviewer's version of D1. Keep the derivation (no new state, and `_amend_record()` keeps `HEAD`'s parent) instead of the recording the plan and the open question pointed at. If you want recording instead, it becomes a new step in `cmd_land`, and the test would pin the record.

**For the person at ship.** Look at these first:
1. `_land_diff()` and `_NO_FORK` at `plugins/factory/scripts/factory.py:2495–2511`, and their two callers at about lines 2470 and 2487. The question is whether the merge base really is the round's rebase point in every landing path, including a rebase onto a base that moved again mid-round.
2. The four-line paragraph copied into `reviewer-code.md`, `reviewer-security.md`, `reviewer-test.md` and `verifier.md`. The four copies should be word-for-word the same.
3. `tests/test_land.py`'s two new tests. One of them also checks that `land-close` still reports `moved`.

- IMPACT: patch — a factory landing no longer stops on a false finding when the base branch moves during the round. Nothing a user does or configures changes.

There is no `notes.md` in the change folder, so there are no undone items to dispose of. The prompt named no irreversible paths, and the plan's Rollback is a plain `git revert`, so no RECOVER lines are needed.
