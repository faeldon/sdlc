I've done round 3: `unmark()` is now wired into core. `sync` sends an issue back to triage when it has left a change's `closes:` line and nothing else records it. The full gate passed: 2199 tests passed, 9 skipped. Everything is uncommitted.

**What changed:**
- **When it runs:** while syncing a change, core lists the open issues once. It unmarks an issue only if all of these hold:
  - it still has the `triaged` label;
  - it has the comment core left when this change took it on;
  - it is no longer on the change's `closes:` line;
  - nothing else in the repo records it (an inbox entry, another change, or a triage verdict).

  That keeps it off issues a person labelled by hand and issues another record has taken over. It runs only if the tracker has both `unmark()` and `open_marks()`.
- **What the issue gets:** one comment ("001-thing no longer takes this issue on; it is open for triage again."), the `triaged` label removed, and its parent cleared. Running sync again doesn't add another comment.
- **Dropped changes** were already covered: GitHub's tracker unmarks their `closes:` issues when the change is closed. Nothing changed there.
- **Not in close's marking pass, on purpose:** that pass runs after the Close commit but before the push that closes the change's issues. It would send just-fixed issues back to triage.
- **Cost:** every `sync` now does one listing of all open issues with their comments, even for a change that never had a `closes:` line.

**Test added:** `test_sync_sends_an_issue_that_left_the_closes_line_back_to_triage`. An issue taken off the line loses its label and parent and gets exactly one comment across two syncs. An issue still on the line, one an inbox entry now records, and one labelled by hand all keep their label. It failed before the code existed because the label stayed.

**Docs:**
- `docs/CONTRIBUTING.md`: `unmark()` is now an optional method in the tracker list, saying when core calls it. The "core doesn't call it yet" note is gone.
- `docs/REFERENCE.md`: the intake paragraph says sync sends a withdrawn issue back to triage.
- `recorded_issues()`'s docstring already named `unmark()`, and is now accurate.

**`plan.md`:** adds the sync step and the reason close's pass isn't used, the new test, a fourth step in the work order, and a rollback note. A revert won't restore labels or delete comments already changed on GitHub; that's done by hand.

**`notes.md`:** the `unmark()` item is ticked. One new unticked item: if a record is removed by hand (for example an entry's `Issue:` line), close's and `mark-triaged`'s marking pass still leaves that issue as `dangling` rather than unmarking it. Fixing that would need `closed_by()` on the unpushed commits to tell a just-fixed issue from a withdrawn one.

- DECISION: [default] (supersedes D1) Call `unmark()` from `sync`, only for an issue this change marked that has left its `closes:` line and that nothing else records, and leave close's marking pass alone. Options: sync only; also close's and `mark-triaged`'s pass; a new command. Going ahead with sync only: close's pass would send just-fixed issues back to triage before the push closes them.
- DECISION: [default] Accept one listing of every open issue with its comments on each `sync`, even for a change with no `closes:` line. Options: always list; skip it when the change's intent never named an issue (would need git history and would miss uncommitted edits). Going ahead with always listing: it is one `gh issue list`.

## Evidence

$ uv run --group dev pytest -q tests/test_archive.py -k left_the_closes_line   (before the code)
FAILED tests/test_archive.py::test_sync_sends_an_issue_that_left_the_closes_line_back_to_triage
1 failed, 142 deselected in 12.22s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py
143 passed in 123.51s (0:02:03)
exit: 0

$ ./check.sh
All checks passed!
2199 passed, 9 skipped in 122.09s (0:02:02)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py accept 116 | grep -E '"passed"'
      "passed": true,
      "passed": true,
  "passed": true,
exit: 0
