DECISION: READY

**Why:** All six fixes the intent asks for (52, 56, 57, 58, 69, 70) are built, each with a test that was seen failing first. Round 2's gate passed on `./check.sh` with 2201 tests. Round 1 had one finding left after verification: the code reviewer found that the board's `_stopped()` was a second copy of `sdlc.factory_stop()`. Round 2 fixed it, and the code, ui and ux reviewers all returned `VERDICT: PASS`. What is left in `notes.md` is minor and was already there before this change.

**Open items:**
- None. No CHANGE from round 2 is still open.

**Decisions to confirm:**
- None. There is no `decisions.md`, and the builder raised no decisions. One thing is unsettled in `intent.md`: its open question (should an unreadable stop record read as a stop or as a problem?) is still not struck through. The intent's own Approach answers it by taking `status`'s way, and the build follows that. Strike the question at ship if you agree.

**For the person at ship:**
- **The changed test in `tests/test_board.py`.** `test_an_unreadable_stop_record_is_a_problem` (from change 086) became `test_an_unreadable_stop_record_is_a_stop_as_in_status`. This is the pinned behaviour the intent said would change, and the new test checks the card against `sdlc.factory_stop(folder)`. Make sure this really is the side you want.
- **`next_action()` in `scripts/board.py`.** A card that is stopped *and* waiting on a decision names only the stop in its `next:` line. The decision still shows on the `needs you:` line. The ux and code reviewers both noted this as falling short of 70's "the next step follows `needs you:`". Neither raised it as a change, and it isn't in `notes.md`. Decide whether it's acceptable or worth its own seed.
- **The page in a browser.** Nobody has opened it. The fixed column headings were checked in screenshots at 1280px and 390px. The empty column's "nothing waiting here" line and the rebasing card's `--abort` wording have only been read in code.
- **The `docs/REFERENCE.md` board section.** The builder edited it outside the plan, and `plan.md` now records the edit.

- IMPACT: patch — the board and `status` now say the same things more plainly, and a person gets clearer next steps, but there is nothing new to do and nothing anyone must change.

- UNDONE: pre-existing: `scripts/board.html:82`: `.next code` has no `overflow-wrap`, so a long unbroken token in a next step could push past a narrow card. None appears in these shots, so this is for later, not a change. → seed: Wrap long tokens in a card's next step
- UNDONE: pre-existing: `scripts/board.html:292`: a stop's `next:` is a long run-on command in monospace (006's "rerun /sdlc-factory:build 006, whose one mend asks again…"), and it wraps badly at 390px. The text comes from the factory's stop record, which this change doesn't touch. → seed: Shorten the factory's stop NEXT: wording for phone-width cards
- UNDONE: pre-existing: scripts/board.py:393: `if entry.get("stopped") or (folder / STOPPED).is_file() and entry["stage"] == "build":` mixes `or` and `and` with no parentheses. The `and` binds first, so it reads as intended, but it is easy to misread. This line is in `_progress()`, which this change doesn't touch. Parenthesise it when someone next edits `_progress()`. → seed: Parenthesise the stop test in board.py's _progress()
- UNDONE: pre-existing: scripts/sdlc.py:4108: a stop waiting on the person reads `needs you: stopped: mend`, and `mend` is the factory's word for a re-run of the reviewer, not something a person knows. The card's `next:` line spells out the step, so the person can still act, but the label is not plain. → seed: Say "stopped: mend" in plain words on the needs-you line
