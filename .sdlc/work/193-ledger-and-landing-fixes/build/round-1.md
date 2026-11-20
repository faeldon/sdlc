I built all five items in this Tier 1 change, and the tests for every file I touched pass. Everything is uncommitted on the change's branch. I didn't run the whole suite; the gate runs that next.

I wrote `plan.md` first, because the Approach touches more than a couple of files.

## Slices
1. **A question that continues in sub-bullets keeps every line** (bug 2026-11-19-79). A new `question_lines()` in `factory.py` reads the lines indented under a `- DECISION:` line, including blank lines between them, until the `- OPTION:`/`- WHY:` run starts. `raised_decisions()` joins them into the question with single spaces, drops their bullet markers, and reads the options and why from after them. Each raise also keeps its first line on its own, so `cmd_decisions()` recognises a ledger written before this change, which holds only that line. It files nothing new for it and fills in its missing options once. Replies with no continuation lines read exactly as before, and `sub_lines()`, `read_ledger()` and `LEDGER_RE` are unchanged, so `factory_records.py`'s pinned copies still match.
2. **A decision raised twice lands once** (nit 2026-11-20-1). 187's duplicates were reworded, not identical. Identical text was already matched, but the resumed builder's new report replaced the old one, so only the ledger still held the first wording. `cmd_decisions()` now also treats a raise as already filed when it has the same source, kind, options and why as an existing entry.
3. **grep's long-option prefixes are refused** (nit 2026-11-19-74, `landing.py`, sensitive). The read-only list now refuses any grep long option whose name has three or more characters after the `--` and begins `--dereference-recursive`, with or without `=value`. It only gets stricter.
4. **Wording.**
   - The `read_only_command()` docstring now says a program that walks the tree itself is covered only by the grep flags (2026-11-19-72).
   - The `_train_begin()` comment now says why `checks: []` with a hash is safe (2026-11-19-71).
   - The land skill's description now names the slow gate at the tip and the approver's judgement of changed acceptance checks (idea 2026-11-19-68).
   - I also rewrapped `cmd_decisions()`'s docstring and the module docstring.
   - **AGENTS.md is unchanged**: the two long lines from nit 2026-11-19-70 were already rewrapped at the base (both are 99 characters now). `plan.md` says so.

## Tests added
- `test_a_question_in_sub_bullets_keeps_every_line_and_its_options`: uses the shape of 187's D3, a question continued in sub-bullets plus a blank line, then its options. It proves the whole question and its options reach the ledger.
- `test_a_ledger_holding_a_question_s_first_line_is_matched`: proves an existing ledger still reads, nothing is filed twice, its options are filled once, and a rerun changes nothing.
- `test_a_decision_reraised_with_the_same_alternatives_lands_once`: proves a reworded re-raise from the same source files nothing. A different source, different options or a different kind still files a new entry.
- `READ_ONLY_REFUSALS` gains three refused cases: `--der`, `--dereference` and `--dereference-recursive=x`. `READ_ONLY_PASSES` gains two allowed ones: `--directories=skip` and `--de`, which grep itself refuses as ambiguous.
- `test_the_land_description_names_what_a_landing_runs`.

Before the fixes, all the new decision tests and the three new refusal cases failed for the expected reasons (shown in the first two commands under Evidence). The description test also failed before the edit; that run isn't shown below.

## Changes to `plan.md`
Its test list now includes the `--de` case. Otherwise it describes the build as it was done.

## `notes.md`
None written.

- DECISION: [default] Treat a raise from the same source and of the same kind, with the same options in the same order and the same why, as one already filed, even when its question is worded differently. Going ahead with that.
  - OPTION: match on source, kind, options and why — catches a resumed agent's reworded re-raise, as with 187's D1/D4 and D2/D5; two different questions with word-for-word identical alternatives would be filed once
  - OPTION: match identical text only — never merges two questions; does nothing for 187's case, which identical text already covered
  - WHY: the intent's outcome is "a decision raised twice in one reply lands once", and 187's twice-raised decisions were reworded, not identical

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "sub_bullets or first_line_is_matched or same_alternatives"
FAILED tests/test_factory.py::test_a_decision_reraised_with_the_same_alternatives_lands_once
3 failed, 396 deselected in 0.98s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k "read_only_command"
FAILED tests/test_train.py::test_read_only_command[grep --dereference-recursive=x keep .---dereference-recursive=x]
3 failed, 51 passed, 87 deselected in 0.55s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -k "sub_bullets or first_line_is_matched or same_alternatives"
3 passed, 396 deselected in 0.24s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "read_only_command"
54 passed, 87 deselected in 0.16s
exit: 0

$ uv run --group dev ruff check . && uv run --group dev ruff format --check .
All checks passed!
312 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_skills.py tests/test_modules.py tests/test_windows.py tests/test_feature_map.py
905 passed in 30.13s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k "read_only or checks or clearance"
61 passed, 80 deselected in 68.40s (0:01:08)
exit: 0
