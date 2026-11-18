I addressed all three kept changes and the nit. The gate passes: 2410 passed, 13 skipped. Each new or extended test failed before its fix.

**Kept changes:**
- **code C1 (`cmd_intake`):** I removed the `except` entirely: the GitHub tracker's `closed_by()` is just a regex match, so nothing there needs catching. If the unpushed commits can't be read, every dangling issue now gets `waits_on_push: null`, and a new `dangling_unread` field says why, so triage can tell "couldn't read" apart from "nothing is waiting". The triage bullet tells it to offer none of them in that case and to say why. A new test covers this path: `test_intake_never_says_nothing_waits_when_it_can_t_read_the_unpushed_commits` replaces `unpushed_closes()` with a stand-in that returns None. `docs/REFERENCE.md` and the `cmd_intake()` docstring describe the null case.
- **ux C2 (`board.html`):** `paint()` now treats a file holding only whitespace as empty, both for the empty note and for hiding the Raw toggle. `test_an_empty_file_says_so` now also covers `"\n"` and `" \n\t\n"`.
- **ux C3 (triage bullet):** it now reads "An issue an unpushed commit closes (`waits_on_push: true`) is waiting on the push: never offer it again". It tells the person the issue is waiting on the push, which `/sdlc:publish` or close will do. Step 6's report now names each such issue, and says when no dangling issue was offered because of `dangling_unread`. I updated `checks.md` to match.

**Nit (spec skill):** the dialog tests need the question's wording inside the WAIT section, so I kept the blockquote. It is now introduced as a sample of what `start` prints, and the skill says to ask `start`'s question as printed and not copy the sample.

`plan.md` now covers the whitespace case, the `null`/`dangling_unread` path, Step 6, and the sample label. `drift` reports nothing, and nothing is left in `notes.md`. I raised no new decisions this round.

## Evidence

$ uv run --group dev pytest -q tests/test_archive.py -k "can_t_read_the_unpushed"   (before the fix)
E       assert (0 == 0 and [(50, False)] == [(50, None)]
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "empty_file_says"   (before the fix)
E           AssertionError: notes.md
E           assert '' == 'This file is empty.'
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py::test_intake_never_says_nothing_waits_when_it_can_t_read_the_unpushed_commits tests/test_archive.py::test_intake_says_a_dangling_issue_an_unpushed_commit_closes_waits_on_the_push tests/test_board.py::test_an_empty_file_says_so
3 passed in 22.04s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_skills.py
357 passed in 1.29s
exit: 0

$ for n in 1 2; do sh -c "<checks.md block n>"; echo "check $n exit: $?"; done
check 1 exit: 0
check 2 exit: 0
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift | grep -E '"(breaking|refresh|report)"'
  "breaking": [],
  "refresh": [],
  "report": [],
exit: 0

$ ./check.sh
2410 passed, 13 skipped in 194.52s (0:03:14)
✔ Validation passed
exit: 0
