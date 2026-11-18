I resolved the one conflict in `plugins/factory/skills/land/SKILL.md`, but the gate is red: one test fails. That test is in a file I wasn't allowed to edit, so the train needs your answer before it goes on.

**The conflict.** The change before 140 in the train (139, landing-train) had split this step of the land skill into separate `review`, `verify` and `mend` bullets, each with its own `factory.py agent` command. 140 had changed one phrase in the old version of that step, the list of reply problems that cost a mend: "a verdict after a preamble" became "verdict lines that disagree".
- **Kept from 139:** its bullet layout and all three commands (`land-review`, `land-verify`, `land-mend`), unchanged.
- **Kept from 140:** the new phrase, moved into 139's `mend` list. Without it the skill would still call a verdict after a preamble a mend, which 140 made untrue.
- No conflict markers remain. I ran no git command beyond reads.

**Why the gate is red.** The failing test is `tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change`, which came in with 139. It makes change 2's behaviour reviewer put "I ran it first." before its verdict and expects that reply to stay unreadable after one mend, so change 2 is ejected. 140's whole point is that such a reply is now read correctly. So change 2 lands, and the assertion `landed == [001-aa, 003-cc]` fails, getting all three changes instead. The two changes conflict in meaning, not in text: the test's example is out of date, and the code is right.

The fix is to the test, not the code. Its example needs a reply 140 still can't read, which now means verdict lines that disagree. Its `"doesn't open with a VERDICT"` string probably needs checking against `_no_verdict()`'s text too. That text currently says "doesn't open with VERDICT: PASS or VERDICT: CHANGES", with no "a".

- DECISION: [blocking] Let the landing agent also edit `tests/test_train.py` to update 139's unreadable-reply test for 140's parsing? Recommend yes.
  - OPTION: yes, edit the test — change its example reply to two disagreeing verdict lines (e.g. `_verdict("behaviour") + _verdict("behaviour", "CHANGES", ("bb.txt:1: x",))`) and match the ejection reason to `_no_verdict()`'s wording; both changes keep their intent, and the gate goes green
  - OPTION: eject 140 from the train — 139's test stays as it is; 140 is rebuilt on top of 139 later and updates the test then
  - OPTION: drop the test — loses 139's proof that a reply still unreadable after its mend ejects only its own change
  - WHY: 140 deliberately made a preamble readable, so only the test's example is stale; what it proves still holds with an unreadable shape.

## Evidence

$ grep -c '<<<<<<<\|>>>>>>>' plugins/factory/skills/land/SKILL.md
0
exit: 1

$ ./check.sh 2>&1 | tail -8
FAILED tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change
1 failed, 2593 passed, 18 skipped in 86.24s (0:01:26)
exit: 1

$ uv run --group dev pytest -q tests/test_train.py::test_a_reply_still_unreadable_after_its_mend_ejects_only_that_change
E       AssertionError: assert ['001-aa', '002-bb', '003-cc'] == ['001-aa', '003-cc']
tests/test_train.py:847: AssertionError
exit: 1
