# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] pre-existing: `scripts/board.html:82`: `.next code` has no `overflow-wrap`, so a long unbroken token in a next step could push past a narrow card. None appears in these shots, so this is for later, not a change. → seed: 2026-11-17-81
- [x] pre-existing: `scripts/board.html:292`: a stop's `next:` is a long run-on command in monospace (006's "rerun /sdlc-factory:build 006, whose one mend asks again…"), and it wraps badly at 390px. The text comes from the factory's stop record, which this change doesn't touch. → seed: 2026-11-17-82
- [x] pre-existing: scripts/board.py:393: `if entry.get("stopped") or (folder / STOPPED).is_file() and entry["stage"] == "build":` mixes `or` and `and` with no parentheses. The `and` binds first, so it reads as intended, but it is easy to misread. This line is in `_progress()`, which this change doesn't touch. Parenthesise it when someone next edits `_progress()`. → seed: 2026-11-17-83
- [x] pre-existing: scripts/sdlc.py:4108: a stop waiting on the person reads `needs you: stopped: mend`, and `mend` is the factory's word for a re-run of the reviewer, not something a person knows. The card's `next:` line spells out the step, so the person can still act, but the label is not plain. → seed: 2026-11-17-84
