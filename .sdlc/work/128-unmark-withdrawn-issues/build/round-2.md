I fixed both KEPT lines from round 1. They were docs only, so no code changed. The gate still passes: 2338 tests, 13 skipped.

- **KEPT, `docs/CONTRIBUTING.md`:** the tracker section now says close and `mark-triaged` also call `unmark()` and read `closed_by()`. I dropped "`sync`'s" from that list.
  - The `unmark()` entry now covers the full marking pass. It sends back an issue it marked whose record went, unless a commit the base branch hasn't pushed closes it. This is named as `unmark_withdrawn()`, next to `withdraw_issues()`. It needs `open_marks()` and `closed_by()`.
  - The `closed_by()` entry now says the full pass reads it through `unpushed_closes()`, so an issue the push will close is left for the push.
- **KEPT, `docs/REFERENCE.md`:** I replaced the wrong clause with the reviewers' wording: "an issue labelled `triaged` that nothing records anymore, which includes one whose send-back failed, or that waits on that push." I also rewrapped the long line that followed it.

`plan.md` doesn't exist (Tier 1) and `notes.md` hasn't changed. I raised no new decisions this round, and the default from round 1 still stands.

## Evidence

$ ./check.sh
All checks passed!
2338 passed, 13 skipped in 217.49s (0:03:37)
✔ Validation passed
✔ Validation passed
exit: 0
