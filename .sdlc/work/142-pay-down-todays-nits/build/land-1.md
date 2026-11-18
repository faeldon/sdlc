I resolved the conflict in `AGENTS.md` with every change's text kept, but the gate is red: one test in `tests/test_train.py` fails, outside the file I was allowed to edit. The markers are gone and nothing else was touched.

**The conflict was only in the *Closing: `cmd_close()`* paragraph.**
- **Kept from main:** the paragraph had gained a sentence since 142 was built: close holds `_main_lock()` from its merge to the `Close` commit (`_lock_depth()`, `LOCK_HELD_ENV`), and refuses a branch carrying another change's commits (`_carries_others()`). That sentence is in, word for word.
- **Kept from 142:** its edit only rewrapped the paragraph to 100 columns, retiring nit 2026-11-18-25. I rewrapped the merged text the same way; every line is ≤100, the longest exactly 100.
- **140 (`4d6316f`):** its edit to the factory paragraph ("holding verdict or decision lines that disagree, none of them first (`opening()`, …") didn't conflict and is intact at line 247.
- **142's other edit:** the rewrapped *register* paragraph is intact at line 160.
- **141 and 143:** neither touches `AGENTS.md`.

**The red gate:** 2604 passed, 18 skipped, 1 failed: `tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change`. I reran it alone and it still fails.
- **Cause:** a clash in behaviour between 140 and main. The test came in with main's train commit `e15e780`, and none of 140–142's diffs touch the file. Its "unreadable" reply is `"I ran it first.\n\n" + verdict`, a verdict after a preamble. 140's spec R6 makes exactly that shape readable, so the reply now files, and change 002 lands instead of being ejected (`['001-aa', '002-bb', '003-cc']` vs `['001-aa', '003-cc']`).
- **Fix:** the test's fixture needs a reply that is still unreadable under 140, such as verdict lines that disagree with none on the first line (R7). That belongs to 140, or to a fix on the train tip, not to this resolution.

- DECISION: [blocking] Who fixes `test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change`, whose preamble-plus-verdict fixture 140's R6 now reads as a verdict? Recommend ejecting 140 to rework the test's fixture to R7's shape.
  - OPTION: eject 140 to rework the fixture — the fix sits with the change whose behaviour moved; 140 lands a round later
  - OPTION: let this landing agent edit `tests/test_train.py` — the train lands now; it goes past the "edit only the conflicted files" bound
  - OPTION: a follow-up change after the train — the train is unchanged; it can't land while its tip is red
  - WHY: R6 deliberately made that reply shape readable, so the old fixture is out of date, not the code wrong.

## Evidence

$ grep -c '<<<<<<<\|>>>>>>>' AGENTS.md
0

$ grep -n 'holding verdict or decision lines that disagree' AGENTS.md
247:missing it, holding verdict or decision lines that disagree, none of them first (`opening()`,

$ ./check.sh
FAILED tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change
1 failed, 2604 passed, 18 skipped in 138.55s (0:02:18)
exit: 1

$ uv run --group dev pytest -q tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change
E       AssertionError: assert ['001-aa', '002-bb', '003-cc'] == ['001-aa', '003-cc']
1 failed in 9.29s
exit: 1

$ git log --oneline -3 -S'test_a_reply_still_unreadable_after_its_mend' -- tests/test_train.py
e15e780 A landing train: the batch is integrated once, gated once, and its conflicts resolved once
