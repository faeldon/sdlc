VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:2497: `_land_diff()` falls back to `base` when `merge-base` fails (`fork = _git(...) or base`). That puts the branch's tip back into the prompt, which is the bug this change removes, and it does so silently. Fix: when no fork point is found, don't name the tip. Return a refusal from `_land_task` (for example "no fork point between <base> and HEAD: the landing can't be reviewed") so the round stops visibly and the reviewers never see a diff against the moved tip.

- DECISION: [default] (the plan's Approach says to record the base each round was rebased onto, and the spec leaves open whether to read it from the gate record or record it in `land`). The code does neither: it derives the base at prompt time with `git merge-base <base> HEAD`. I'd keep the derivation, since it adds no state and `HEAD`'s parent is kept by `_amend_record()`. Please confirm, because the plan's text and the open question both still point at recording. If you want the recorded version, it's a new step in `cmd_land`, and the test would pin the record rather than the merge-base.

## Notes

- Nit: `plugins/factory/scripts/factory.py:2000`, the `LAND_TASKS` comment still says "the review of the change as it now stands on the base branch". That's no longer true; it now reads the diff from the rebase point.
- Nit: the same four-line paragraph is copied into `reviewer-code.md`, `reviewer-security.md`, `reviewer-test.md` and `verifier.md`. A single source isn't available, since the prompt already carries the diff, so this is acceptable, but the wording should stay identical across the four to keep it that way.
- Nit: `_land_diff`'s docstring says "a later move of the branch leaves where it is". "The branch" here means the base branch, which reads as the change's branch. Say "the base branch".
- Done well: the test rebases, adds a commit to main, and checks both the reviewer and verifier prompts name `git diff <rebased_onto>...HEAD` and not the moved tip. It also asserts the script answers `moved` at close. Before the change, the prompt text fails the first assertion, so the test does guard the fix.
- Not checked: I didn't run `./check.sh` or the full suite, only `tests/test_land.py`. The two new tests and the 50 tests in that file pass.

Tests run: `uv run --group dev pytest -q tests/test_land.py -k "reads_the_change or landing_review"` (2 passed), and `uv run --group dev pytest -q -n auto tests/test_land.py` (50 passed).
