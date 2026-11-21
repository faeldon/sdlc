A one-change train now gates its committed tip like a longer train does. The new tests reproduce the escape and pass after the fix, and the full gate run is green: 3860 passed, 29 skipped. Everything is left uncommitted.

## Slices built

1. **The gate (R1–R5).** In `landing.py`, `_train_gate()` no longer skips a train of one whose stacked commit equals its pre-train commit. Such a train now reads `gate` (prefix 1 of 1) before `close`. Its gate runs through the existing `gate --land` path, so the record goes to `build/land-1.gate.md`. The records ledger now checks a train of one too. A red tip ejects the change with `cause: gate` and `undo` null, and its records are amended in through the existing `_put_back()` and `_train_eject()` path. Only the two shortcut lines changed. All 278 existing tests in `test_train.py` and `test_land.py` passed unchanged, so no existing test needed updating.
2. **`ungated` (R6).** A new helper, `_ungated(main, base)`, reads the base branch each time. It is null when the base names a `[commands] check`; otherwise it is `<base>'s .sdlc/config.toml names no [commands] check`. It is in `_train_reading()`'s output and in `_run_end()`'s summary on both of its branches.
3. **The question (R7).** `land_question(..., gated=True)` replaces the gate clause with `not gated, since <base> names no [commands] check (...)` when `gated` is false. With a check, the wording is unchanged byte for byte. `cmd_land_check()` passes `gated` from `factory._base_check(root, trunk)`, so the change's own config never counts.
4. **The skill and the wording (R8, R9).**
   - In the land `SKILL.md`, Step 3's `gate` bullet now says a train of one is gated, on the commit that lands.
   - Step 3's list of the loop's JSON keys names `ungated`.
   - Step 4 says to report no gate and why when `ungated` is set.
   - The comments in `cmd_land()` and in `factory.py`'s `cmd_gate()` are updated.
   - `docs/REFERENCE.md`'s `gate_fail` sentence now reads "on every change a landing gates".

## Tests added
- `test_a_train_of_one_is_gated_at_its_tip[still|rebased]` covers R1. Before the fix, both cases read `close`.
- `test_a_train_of_one_whose_commit_fails_the_check_is_ejected` covers R2. The check is `! git ls-files | grep -qx forbidden.txt`, and the build round's gate passes it. Before the fix the train closed the change. Now it is ejected, the base doesn't move and nothing closes. The branch stays at its landing commit, holding `land-1.gate.md` (`GATE: FAIL`) and an ejection row with `cause: gate`.
- `test_a_green_train_of_one_records_its_tip_gate` covers R3: `gates: 1`, `ungated` null, and a `GATE: PASS` file and `TIP GATE: PASS` line in the landed commit.
- `test_train_run_stops_on_a_hand_written_record[gate-of-one]` covers R4. Before the fix it never stopped, since no gate reading came.
- `test_a_landing_with_no_check_says_it_ran_no_gate` covers R6, for both a reading and the loop's exit JSON.
- `test_the_landing_question_names_only_what_the_batch_holds` gains the ungated wording. `test_land_check_words_an_ungated_question[no-check|check]` is new; in its no-check case the change's own config names a check, which is ignored. Both cover R7.
- `test_land_reports_an_ungated_landing` covers R8.

## Named tests run
- The R1–R4 and R6 tests failed 6 and passed 2 before the fix. The 2 that passed are the existing hand-written-record cases. After the fix, all 8 passed.
- `test_train.py` and `test_land.py` in full: 278 passed, 1 skipped.
- The board, indicators and modules tests: 420 passed, 28 skipped.
- The R7 tests failed 2 before the fix; with the R7 and R8 tests together, 4 passed after.
- The R8 test failed before the skill edit; `test_skills.py` in full then passed, 474.
- ruff check and ruff format are clean, and the spec's grep finds nothing.

## Changes to `plan.md`
The scaffold is replaced with the plan. After the build, the plan's step 4 also covers the `gate` bullet edit in Step 3, and the Tests section gives the exact parametrize ids.

## `notes.md`
Nothing left.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "train_of_one_is_gated or commit_fails_the_check or green_train_of_one or no_check_says or hand_written_record"   (before the fix)
FAILED tests/test_train.py::test_a_train_of_one_is_gated_at_its_tip[rebased]
FAILED tests/test_train.py::test_train_run_stops_on_a_hand_written_record[gate-of-one]
FAILED tests/test_train.py::test_a_green_train_of_one_records_its_tip_gate - ...
FAILED tests/test_train.py::test_a_landing_with_no_check_says_it_ran_no_gate
FAILED tests/test_train.py::test_a_train_of_one_is_gated_at_its_tip[still] - ...
FAILED tests/test_train.py::test_a_train_of_one_whose_commit_fails_the_check_is_ejected
6 failed, 2 passed in 10.70s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "train_of_one_is_gated or green_train_of_one or no_check_says or hand_written_record" 2>&1 | grep -E "^E  .*(Assert|assert)"   (before the fix)
E       AssertionError: ['commit', 'close']
E       assert ('close', '001-aa') == ('gate', '001-aa')
E       AssertionError: {'under_way': True, 'next': 'done', 'change': None, 'worktree': None, ...}
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_train.py -k "train_of_one_is_gated or commit_fails_the_check or green_train_of_one or no_check_says or hand_written_record"   (after the fix)
8 passed in 10.12s
exit: 0

$ uv run --group dev pytest -q -n 6 tests/test_train.py tests/test_land.py
278 passed, 1 skipped in 191.92s (0:03:11)
exit: 0

$ uv run --group dev pytest -q -n 6 tests/test_board.py tests/test_indicators.py tests/test_modules.py
420 passed, 28 skipped in 23.98s
exit: 0

$ uv run --group dev pytest -q -n 3 tests/test_land.py tests/test_train.py -k "landing_question_names_only or ungated_question"   (before the fix)
FAILED tests/test_land.py::test_the_landing_question_names_only_what_the_batch_holds
FAILED tests/test_land.py::test_land_check_words_an_ungated_question[no-check]
2 failed, 1 passed in 4.30s
exit: 1

$ uv run --group dev pytest -q -n 3 tests/test_land.py tests/test_train.py -k "question"
5 passed in 5.52s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k ungated_landing   (before the skill edit)
FAILED tests/test_skills.py::test_land_reports_an_ungated_landing - Assertion...
1 failed, 473 deselected in 0.44s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_skills.py
474 passed in 1.67s
exit: 0

$ grep -rn "gated as its build was\|lands on its round's gate alone" plugins/ docs/ AGENTS.md
exit: 1

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
335 files already formatted
exit: 0

$ uv run --group dev pytest -q -n 6 tests/test_train.py -k "train_of_one_is_gated or commit_fails_the_check or green_train_of_one or no_check_says or hand_written_record"   (after formatting)
8 passed in 28.41s
exit: 0

$ uv run --group dev pytest -q -n 3 tests/test_land.py::test_the_landing_question_names_only_what_the_batch_holds tests/test_land.py::test_land_check_words_an_ungated_question tests/test_skills.py::test_land_reports_an_ungated_landing
4 passed in 2.48s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 217
All checks passed!
3860 passed, 29 skipped in 250.73s (0:04:10)
✔ Validation passed
✔ Validation passed
exit: 0

$ git diff --stat
 docs/REFERENCE.md                    |   4 +-
 plugins/factory/scripts/factory.py   |   5 +-
 plugins/factory/scripts/landing.py   |  53 +++++++++++-----
 plugins/factory/skills/land/SKILL.md |  10 +--
 tests/test_land.py                   |  34 +++++++++++
 tests/test_skills.py                 |  10 +++
 tests/test_train.py                  | 115 +++++++++++++++++++++++++++++++++--
 7 files changed, 201 insertions(+), 30 deletions(-)
exit: 0
