## Report: 131 land-gate-shows-the-change, build round

The landing's dialog now shows what each change is and what its yes will file, and the full gate passes (2338 tests). Everything is left uncommitted in the worktree for `/sdlc:ship`.

**Plan.** I wrote `plan.md` first: the Approach touches the script, the land skill and the tests. The build matches it. Change 125 hasn't landed, and its build skill reads the intent itself rather than through a reader in the script. So there was nothing to share: this change has its own reader and no `depends_on: [125]`.

**Slices built**
1. **What each change is.** A new `intent_parts(folder)` in `factory.py` quotes the intent's title (without its `NNN — ` number), Problem and Outcome as written. It reuses the existing `_section()`. `land-check` adds this as `intent` to every batch entry, and to every excluded one, since those copy the entry.
2. **What the yes approves.** A new `land_shown(batch)` renders the text the question calls "as shown". Each change is listed by name and title, followed by only the parts it has:
   - its acceptance checks (`name: command`)
   - its skills' cases and their cap
   - each undone note with its disposition (`→ seed: …`, the bug's `filed as a bug, <severity>: <title> (<paths>)`, or `→ dropped: …`)
   - each assumed decision (`D<n>: <text>`)
   - its `How to recover:` lines

   `land-check` prints this as `shown`, which is `null` when the batch is empty. `land_question()` and what a yes approves are unchanged, and `land-check` still writes nothing.
3. **The land skill.**
   - Step 0 describes `intent` and `shown`.
   - Step 1 opens each change with its intent, quoted and never summarised; signals and parts follow.
   - Step 2 asks `question` literally as before, and passes `shown` as the `preview` of the `yes` and `yes, with a fix` options, so it appears inside the dialog. Where no dialog can be shown, the question is asked right after `shown`.

**Tests added** (`tests/test_land.py`). All four failed before the code existed, on the missing function and keys.
- `test_intent_parts_quote_the_title_problem_and_outcome` checks that the intent is quoted exactly, and that a folder with no intent gives empty parts.
- `test_the_dialog_shows_each_disposition_and_assumed_decision` fixes the exact text shown for a batch with a seed, a bug, a drop, an assumed decision, a check, cases and a recovery line, plus a change that has none of them (shown by its title alone).
- `test_land_check_shows_each_changes_checks_cases_notes_decisions_and_recovery` (extended) checks that `land-check` gives each change its `intent`, and that `shown` holds the title, the seed, the drop and D1.
- `test_a_landing_files_each_approved_bug_once` (extended) checks that `shown` holds the bug's disposition when it comes through `land-check`.

**Gate:** `./check.sh` is green: ruff clean, 246 files formatted, 2338 passed and 13 skipped, plugin validation passed. My first run in the background hit the tool's 10-minute limit and was stopped before it printed a result. A rerun with a longer limit is the one shown below.

**notes.md:** nothing left over.

- DECISION: [default] Show `shown` as the `preview` on the `yes` and `yes, with a fix` options, with no change to the question's text? Options: preview on the yes options; put the block in the question's own text; show it only above the dialog. Going with the preview: it puts the detail in the dialog without changing the literal question.
- DECISION: [default] Show each change's whole intent (title, Problem, Outcome) in Step 1 above the dialog, and only its title in the dialog's `shown`, whatever the batch size? Going ahead with this unless told otherwise.
- DECISION: [default] Quote Problem and Outcome in full, with no length cap? Going ahead in full: the intent says quote, never summarise.
- DECISION: [default] Should `shown` also hold checks, cases and `How to recover:` lines, not only dispositions and assumed decisions? Going ahead with all of them: the question says "as shown" or "shown" about each one.

## Evidence

$ uv run --group dev pytest -q tests/test_land.py -k "intent_parts or dialog_shows or land_check_shows or files_each_approved_bug"   (before the code)
FAILED tests/test_land.py::test_land_check_shows_each_changes_checks_cases_notes_decisions_and_recovery
FAILED tests/test_land.py::test_intent_parts_quote_the_title_problem_and_outcome
FAILED tests/test_land.py::test_the_dialog_shows_each_disposition_and_assumed_decision
FAILED tests/test_land.py::test_a_landing_files_each_approved_bug_once - KeyE...
4 failed, 54 deselected in 97.33s (0:01:37)
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "intent_parts or dialog_shows or land_check_shows or files_each_approved_bug"   (after)
4 passed, 54 deselected in 15.29s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -n auto
58 passed in 146.38s (0:02:26)
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py
354 passed in 0.54s
exit: 0

$ ./check.sh > /tmp/131-gate.log 2>&1; echo "exit: $?" >> /tmp/131-gate.log; grep -E "passed|failed|All checks|formatted" /tmp/131-gate.log
All checks passed!
246 files already formatted
2338 passed, 13 skipped in 64.00s (0:01:03)
✔ Validation passed
✔ Validation passed
exit: 0
