I've dealt with all nine nits: seven are fixed and two are retired with their reasons. `./check.sh` passes with 2549 tests (18 skipped), and everything is uncommitted on the branch for `/sdlc:ship`.

**Plan:** this is a Tier 1 change, but it touches more than a couple of files, so I wrote `plan.md` first. The line numbers in the nits had moved since they were filed, so the plan finds each one by its text. Two items turned out differently from what the plan expected: the `# fmt: skip` nit (28) and the reviewer-ux nit (35).

**What each nit got:**
- **25:** reflowed the *Closing* and *The register* paragraphs in `AGENTS.md` at 100 columns. A word-by-word diff against `HEAD` shows the wording is unchanged.
- **28:** retired, already done. The `out["dangling"]` code landed in 138 without a `# fmt: skip`, so there was nothing to remove.
- **29:** rewrapped triage's Step 6 paragraph, wording unchanged.
- **30:** removed the "138 C2" label from `tests/test_board.py`. The other label, "138 C1", is actually in `tests/test_archive.py`, which isn't on the intent's list of files; I removed it there too, since it's only a docstring. Both docstrings already state their rule.
- **31:** renamed the test to `test_no_build_question_for_a_refusal_or_a_tier_1_spec`.
- **34:** the `approve` step in the factory's build skill now says `exhausted` is also set when the run stops early as `stuck` or `untestable`, and that the approver is told which. This matches what `factory.py` actually tells the approver.
- **35:** `reviewer-ux.md` needed no edit. Its sentence already matched the other five word for word; the smaller diff was only line wrapping. The test now checks that every reviewer holds the whole sentence (a new `REASK` constant), not just the words "word for word".
- **36:** retired as not testable, with a comment in `test_readme_names_the_light_reviewers_and_models` saying the README's table of changes 124, 125, 129 and 131 is checked by hand against each change's `Close` commit.
- **37:** added the missing case to `test_a_change_kept_twice_escalates_before_the_rounds_run_out`: if round 1 has no `verified.md`, round 2 keeping the same change is not `stuck`.

**Tests added:**
- **The round-without-`verified.md` case (37):** passes now. When I removed the `and prev["verified"]` guard from `early_stop()` for one run, it failed with a `TypeError`, so it does cover that branch. The guard is restored.
- **The whole-sentence check (35):** passes on the real files. It failed when I briefly changed one word in `reviewer-ux.md`, which is restored.

**Left in `notes.md`**, three unticked `- [ ]` items outside this change's scope:
- More lines in `AGENTS.md` run past 100 columns, including the *Writes before a WAIT* paragraph.
- `test_a_server_that_fails_on_its_own_is_started_once` still cites "111 C1", another review-only label.
- One sentence in `reviewer-code.md` and `reviewer-ux.md` (the `supersedes` one) is a single long line.

No decisions raised.

## Evidence

```
$ uv run --group dev pytest -q tests/test_factory.py::test_a_change_kept_twice_escalates_before_the_rounds_run_out
1 passed in 7.13s
exit: 0

$ (guard `and prev["verified"]` removed from early_stop(), then restored) uv run --group dev pytest -q tests/test_factory.py::test_a_change_kept_twice_escalates_before_the_rounds_run_out
E           TypeError: 'NoneType' object is not subscriptable
plugins/factory/scripts/factory.py:2319: TypeError
1 failed in 7.11s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "word_for_word or tier_1_spec"
3 passed, 303 deselected in 7.40s
exit: 0

$ (reviewer-ux.md's "stops for the" changed to "halts for the", then restored) uv run --group dev pytest -q tests/test_factory.py -k word_for_word
FAILED tests/test_factory.py::test_the_review_prompt_asks_for_an_undone_kept_change_word_for_word
1 failed, 305 deselected in 0.25s
exit: 1

$ diff <(git show HEAD:AGENTS.md | tr -s ' \n' '\n\n') <(tr -s ' \n' '\n\n' < AGENTS.md) && echo same-words
same-words
exit: 0

$ diff <(git show HEAD:skills/triage/SKILL.md | tr -s ' \n' '\n\n') <(tr -s ' \n' '\n\n' < skills/triage/SKILL.md) && echo same-words
same-words
exit: 0

$ ./check.sh
All checks passed!
255 files already formatted
2549 passed, 18 skipped in 67.35s (0:01:07)
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
```
