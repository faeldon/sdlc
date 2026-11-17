# 121 — Plan

> How the change is built, written after reading the code: the files it touches, the order of the
> work, the tests and what each proves, and what a revert wouldn't undo.

## Files to change

- `plugins/factory/scripts/factory.py`: `_land_task()`'s `land-review` and `land-verify` prompts
  name the diff from a new `_land_diff()`, `git diff <fork>...HEAD`, where `<fork>` is
  `git merge-base <base> HEAD` read when the prompt is built. That is the commit the round rebased
  the change onto: the base only moves forward from it, and the amend that adds the landing's
  record keeps `HEAD`'s parent, so a later move of the base never moves it. No new record is
  written. Reuses `_git()` and `_base()`. With no merge base, both tasks refuse
  (`_NO_FORK`) rather than name the branch's tip (round 1's review).
- `plugins/factory/agents/reviewer-code.md`, `reviewer-security.md`, `reviewer-test.md`,
  `verifier.md`: one paragraph each, that a landing round's change is committed and its diff is the
  one the prompt names, never one against the base branch as it is now. The behaviour, UI and UX
  reviewers read no diff, so they're unchanged.
- `tests/test_land.py`: the test below.

## Work order

1. One slice: the test, then `_land_diff()` and both prompts, then the agents' wording.

## Tests

- `test_a_landing_review_reads_the_change_from_its_rounds_own_base`: rebases a change in a
  landing, moves the base branch again, and checks both landing prompts name
  `git diff <the round's base>...HEAD` and never the moved tip, that this diff holds the change's
  file and not the later commit's, and that `land-close` still reports the move as `moved`
  (the move is caught by the script, the constraint that a base which really moved still goes
  back through a round).

- `test_a_landing_review_with_no_fork_point_is_refused`: with `merge-base` finding nothing, both
  `land-review` and `land-verify` refuse, naming the missing fork point, and give no prompt.

## Rollback

Nothing outside the code: no data written, nothing published. `git revert` undoes it.
