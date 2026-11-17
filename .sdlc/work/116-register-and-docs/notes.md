# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Left for later

- [x] `recorded_issues()`'s docstring names the tracker's `unmark()` among what sets its records,
  but core never calls `unmark()` (only GitHub's tracker has it, and its test calls it directly):
  either wire it in where a record is withdrawn (a drop, a change no longer closing an issue) or
  take it out of the docstring. Done in round 3 (R1): `sync` calls it through
  `withdraw_issues()`; a drop already reached it through `archive()`.
- [x] A full marking pass (close, `mark-triaged`) still leaves a core-marked issue whose record → seed: 2026-11-17-89
  went (an entry's `Issue:` line removed by hand) as `dangling` for triage, not unmarked: close's
  pass runs between its Close commit and the push that closes the change's issues, so it would
  need `closed_by()` on the unpushed commits to tell a just-fixed issue from a withdrawn one.
