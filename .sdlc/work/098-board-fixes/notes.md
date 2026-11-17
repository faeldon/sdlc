# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

- [x] ux: scripts/board.py:601-605: the stage-missing check runs before the rebasing check, so a rebasing change whose `intent.md` won't read gets "fix intent.md's frontmatter" and no word that its rebase is stopped. That is the case the comment at 603-604 names ("its conflicted files may be what won't read"), and a conflict in `intent.md` is exactly how it happens. Move the `entry.get("rebasing")` branch above the `problems and stage is None` check so every rebasing card gets the resolve/abort line first. Done in round 3, with every pair of `next_action()`'s states pinned (`PRECEDENCE` in `tests/test_board.py`).
- [x] pre-existing: scripts/board.html: the `.col-head` row lets the "who" subtitle wrap beside the heading, so the Test column's "the gate and the review" sits indented under a one-line title and looks misaligned at 1280px. Filed for later. → seed: 2026-11-17-52
- [x] pre-existing: board.html:146: the drawer has `aria-modal` but no focus trap, so Tab can leave it while it is open. Filed for later. → seed: 2026-11-17-53
- [x] pre-existing: at 390px the columns stack in board order, so Needs you sits below every Plan and Build card and is off-screen on a phone. This change doesn't alter it; filed for later. → seed: 2026-11-17-54
- [x] pre-existing: at 390 wide the columns stack in order, so Needs you (the column a person must act on) sits below Plan, Design and Build, about five cards down. A phone user has to scroll past all of it to find the card that needs them. Filed for later, not this change's rework. → seed: 2026-11-17-55
- [x] pre-existing: an empty column (DESIGN, TEST, READY TO SHIP, READY TO CLOSE in the screenshots) shows a bare "—". It does not say the column is empty or that nothing is waiting there. → seed: 2026-11-17-56
- [x] code (round 2 note): a card with a problem and a pending decision at `build` names only "fix what its problems name", by the precedence in `plan.md`; it no longer says a decision is waiting too. The card's other lines still show `pending`; whether its next step should name both is for ship. → seed: 2026-11-17-57
- [x] code (round 2 note): the rebasing card's `--abort` wording doesn't say `resolve --abort` keeps the resolved work under `refs/sdlc/end/<branch>`. → seed: 2026-11-17-58
