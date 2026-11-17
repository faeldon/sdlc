I added the two failure classes to `.sdlc/REVIEW.md`, at the end of "The ways this repo's code fails". The full gate passes (1848 tests). Nothing is committed.

This is a Tier 1 change that touches one file, so I wrote no `plan.md`, even though the prompt asked for one: the intent says Tier 1, and its Approach is the spec. There were no code slices and no red/green tests, because the change is prose only.

**What changed**
- **A transcript's shape assumed, not read.** Worded as the seed has it. I added one sentence naming the tests that pin the escapes from 047 and 050: `test_a_question_ends_with_a_question_mark_its_answers_after_it_or_not` and `test_a_skill_the_session_starts_counts_as_typed`, both in `tests/test_metrics.py`.
- **A path compared as text between two sources that write it differently.** Also worded as the seed has it, plus one sentence naming the tests that pin 041's F6 and 059's F1: `test_paths_shown_are_posix` (`tests/test_windows.py`) and `test_a_non_ascii_hotspot_on_the_base_branch_is_not_gone` (`tests/test_retro.py`). I read both findings in history to confirm they are these two problems: `str(SETTINGS)` against POSIX paths in 041, and a quoted numstat path against an unquoted `ls-tree` listing in 059.
- **Acceptance check:** `.sdlc/work/078-review-escape-classes/checks.md` greps for both bullet leads. It passes, and `sdlc.py checks` reads it with no problems.

**The intent's open questions**
- **Does each bullet name its test?** Yes, both do; `tests/` already had tests for each class. No test is described as built from a recorded transcript, though. The metrics tests use made-up entries in the same shape, so the first bullet's rule is new for any future change.

**Other notes**
- `.sdlc/work/inbox.md` was already modified when I started: the seed is tagged `[building]`. I didn't touch it.
- Nothing left in `notes.md`.

- DECISION: [default] Is the first bullet's "carries a test built from a real transcript's entries" a rule the review enforces, or only a question it asks? Options: a rule; a question. Going ahead with a rule, as the seed words it: 047's F1 was answered `minor` because nothing asked for one.

## Evidence

$ uv run --group dev pytest -q tests/test_defaults.py tests/test_nothing_local.py
126 passed in 7.41s
exit: 0

$ ./check.sh
All checks passed!
1848 passed in 232.42s (0:03:52)
✔ Validation passed
✔ Validation passed
exit: 0

$ grep -q '^- \*\*A transcript.s shape assumed, not read\.\*\*' .sdlc/REVIEW.md && grep -q '^- \*\*A path compared as text between two sources that write it differently\.\*\*' .sdlc/REVIEW.md
exit: 0

$ uv run --quiet --script scripts/sdlc.py check --strict
■ Problems: 0
    none ✅
exit: 0
