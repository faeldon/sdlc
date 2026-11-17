All five conflicted files are resolved with no markers left, and the full gate passes: 2137 tests passed, 9 skipped, and both validations passed. I ran no git command, so the files are ready for `factory.py` to stage and continue the rebase.

The base branch had landed new landing behaviour: acceptance checks and skills' cases run at landing (`accept`, `cases`), undone notes and assumed decisions settled after the yes (`_dispose`), `How to recover:` lines, the batch's question now worded by the script (`land_question()`), and `preflight` read once (`pre`). This change adds following a moved base branch, recording paths no review read, and the fix at landing. Every resolution below keeps both.

**`.sdlc/work/inbox.md`**
- **From the base branch:** the register as it stands there. Seeds 29, 30, 35, 36, 39 and 40 are gone from it, so they stay gone.
- **From this change:** seeds 37 and 38 keep their `[building]` tag and their `Building in .sdlc/work/104-landing-follows-main/.` line.

**`plugins/factory/README.md`**
- **From the base branch:** the paragraph keeps the new signals (acceptance checks, skills' cases in scope, undone notes), "open or assumed decision", the question showing what the yes approves, and the irreversible-path exclusion.
- **From this change:** the follow loop, `yes, with a fix` with your words going to `decisions.md`, `unreviewed=<n>`, and the two new signals.
- The command list names `land-fix` next to the base branch's `accept` and `cases`.

**`plugins/factory/skills/land/SKILL.md`**
- **Signals:** the base branch's list (checks, cases, undone notes) plus this change's (changed since the last snapshot, a fix made while landing, the `unreviewed=` line).
- **The question:** the base branch's full form, with this change's "as often as it moves while landing, up to `<moves>` times", the fourth answer `yes, with a fix`, and the `<moves>` note.
- **After the yes:** the base branch's "to change a disposition, leave it out" sentence, followed by this change's `yes, with a fix` handling.

**`plugins/factory/scripts/factory.py`**
- **`land_signals`:** the signature takes both, `pre: dict | None = None, unreviewed=()`, and the docstring covers both.
- **`cmd_land` and `cmd_land_check`:** they call `_preflight` as the base branch does, and pass `unreviewed=` by keyword.
- **Kept whole:**
  - from the base branch: the helpers (`_preflight`, `read_proposals`, `unrecovered`, `land_parts`, `accept_path`, `accept_build`, `_accept_state`, `cmd_accept`, `_note_says`, `_note_line`, `cmd_cases`);
  - from this change: `land_unreviewed`, `UNREVIEWED_UNKNOWN` and `_unreviewed_at_test`.
- **`land_message`:** the base branch's paragraphs (Retired nits, Carried forward, Dropped, How to recover), then this change's unreviewed paragraph, then the trailer with `unreviewed=` when there is one.
- **`land_verdict`:** its output carries both `fixed` and `accept`. A fix round on a change with checks therefore reruns them too.
- **argparse and dispatch:** `accept`, `cases` and `land-fix` all stay.
- **Beyond the markers:** the base branch's new `land_question()` worded the question without this change's clause or fourth answer. I gave it `moves` (defaulting to the `[land] moves` default) and the follow clause plus `yes, with a fix`. `cmd_land_check` now passes `cfg["land"]["moves"]`.

**`tests/test_land.py`**
- **Both sets kept:** the base branch's checks-and-cases tests, then this change's follow-main, unreviewed and fix tests.
- **Strings updated:** the two exact strings in the base branch's `test_the_landing_question_names_only_what_the_batch_holds` now carry the merged question.
- **New assertion:** `land.moves` reaches the question.

Two things to know:
- **A slip during the resolution:** my first pass doubled the backslashes in the base branch's accept helpers. Five of the base branch's tests caught it, I fixed it, and the gate run below is clean.
- **`spec.md` and `plan.md` not updated:** they weren't among the conflicted files, so they still quote the question as it read before the base branch moved. It is now composed by `land_question()`.

## Evidence

$ ./check.sh   (before fixing the doubled backslashes)
FAILED tests/test_land.py::test_factory_accept_records_sdlc_accepts_verdict
FAILED tests/test_land.py::test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone
5 failed, 2132 passed, 9 skipped in 52.57s
exit: 1

$ grep -rn '^<<<<<<<\|^=======$\|^>>>>>>>' .sdlc/work/inbox.md plugins/factory/README.md plugins/factory/scripts/factory.py plugins/factory/skills/land/SKILL.md tests/test_land.py | wc -l
0
exit: 0

$ ./check.sh
All checks passed!
2137 passed, 9 skipped in 57.37s
✔ Validation passed
✔ Validation passed
exit: 0
