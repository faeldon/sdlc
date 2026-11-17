I've resolved all three conflicts, keeping both sides' intent in each file. No conflict markers remain and the full gate passes: 1986 tests passed, ruff and both plugin validations clean. As asked, I edited only those three files and ran no git command.

**`.sdlc/work/inbox.md`.** Both sides were removing entries, so the conflicted section now holds none of them:
- **Base side:** it had retired entries 2026-11-17-14 (the board tests' port 0), -17 (the `inbox-commit` mislabel) and -18 (the reviewer preamble). The 094 work shipped those.
- **This change:** it deletes its own seed, 2026-11-17-16 ("Resume an escalated factory run"), as shipping a change does with its idea.
- Every entry around them stays as base has it, including the -11 nit and -19.

**`docs/REFERENCE.md`, the board paragraph.**
- **Base side:** I kept base's newer wording whole. It covers 086's rule that a factory signal only counts at its own stage, the stage being the only mark of the person's answer, and 091's hand-run gate moving a card to Test, with its `gate green` / `gate red` badge.
- **This change:** I added its point into that text. The ESCALATE that puts a card in Needs you is the one in its current `decision.md`. A change sent back to the factory keeps the old decision as `decision-<n>.md`, a file in its folder, and is in Build again.

**`tests/test_board.py`.** Both sides only added tests at the end of the file, so I kept them all:
- **Base side:** its `_escalated` helper and two tests, `test_each_factory_signal_counts_only_at_its_stage` and `test_a_file_that_wont_read_needs_the_person_at_any_stage`.
- **This change:** `test_a_restarted_factory_card_is_in_build_with_its_old_decision_as_a_file`, which still passes under base's stage-gated columns.

## Evidence

$ grep -n '^<<<<<<<\|^=======$\|^>>>>>>>' .sdlc/work/inbox.md docs/REFERENCE.md tests/test_board.py
(no output)
exit: 1

$ ./check.sh
All checks passed!
211 files already formatted
1986 passed in 39.33s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k "restarted or each_factory_signal or wont_read"
3 passed, 45 deselected in 5.45s
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
