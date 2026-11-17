- KEPT: code: C1: docs/CONTRIBUTING.md:193: the paragraph says core reads the rest of the list only from a tracker with `intake()`, and that one without it reads no issues at all. That is wrong for close. `cmd_close`'s record step (scripts/sdlc.py ~4732) calls `mark_issues()` whenever the tracker has `mark()`. `mark_issues()` then calls `open_marks()` or `open_numbers()` without going through `_intake_tracker()`.

## Notes
- I ran nothing. I read `cmd_close`, `_intake_tracker`, `mark_issues` and the new paragraph in the diff.
- `_intake_tracker()` is called from `cmd_intake`, `cmd_closes`, `cmd_mark_triaged`, `cmd_needs_info` and `cmd_sync`. In `cmd_sync`, only the marking of a change's `closes:` issues is gated; the mirroring itself goes straight to the tracker.
- The rewording should therefore not describe `sync` as wholly gated by `intake()`. It should also list `closes` (which calls `titles`) rather than only the commands named in the change.
