DECISION: ESCALATE

**Why.** The two rounds ran out with one change still open, so the skill only accepts ESCALATE. Since my last escalation you took path (b), and that resolved nearly everything:
- **Decisions:** D1–D4 are all ticked, and D2 is marked as replaced by D3 and D4.
- **Scope:** the intent's O6 line now claims only the column order, the drawer and the chip.
- **The open item:** the poll problem is named as bug 2026-11-17-50, to be fixed in a change of its own.

The code and ui reviewers passed round 2, and the full `./check.sh` gate passed at round 2 (2001 tests). What's left is for you to confirm that the narrowed scope is how you want this to land.

**Open items**
- ux (round 2, kept by the verifier): `scripts/board.html:293`. The board rebuilds itself whenever the data it is built from changes. Each change's age is counted in whole seconds, so that data differs on every 2-second poll. Every card is rebuilt, keyboard focus drops to the page body, and because `#board` is `aria-live` a screen reader may re-read the whole board. This was already true on `main`; this change only added the narrow-width flag to what triggers a rebuild. The intent now hands it to bug 2026-11-17-50, but its line in `notes.md` is still unticked.
- code and ui (round 2, optional): crossing the 760px width now also rebuilds the board, so focus is lost on a rotation or resize. Same cause as above; fixing the bug fixes this too.
- From `notes.md`: the tests only read the page's source. Nothing runs the drawer's focus trap in a browser.

**Decisions to confirm**
- None. D1–D4 are all decided, and the build follows each of them: the chip shows visible text `verifier: kept N · dropped M`, and the columns are ordered in the page by `columnOrder()` using `matchMedia`.

**For the person at ship**
1. Check that bug 2026-11-17-50 is in the register on `main`. It isn't in this worktree's copy of `.sdlc/work/inbox.md`, which is expected if it went through `inbox-commit`, but the narrowed O6 line depends on it existing. If it's there, tick the ux line in `notes.md`, or say there that it moved to the bug.
2. `columnOrder()` and the `NARROW` listener (`board.html` around 164–172 and 385), which replaced the CSS `order` rule. The page now has no CSS `order:` at all.
3. The drawer's keydown handler: Tab and Shift-Tab wrap inside it, Escape closes it, and `closeDrawer()` finds the card that opened it by `data-change`. That last part means focus returns even after a poll has replaced the card.
4. The chip's visible label and the `.doc` pane's new `tabindex` and label.

## Reconsider the approach

The same thing came back in both rounds: what a keyboard or screen-reader user actually gets lay one layer further out than the code being fixed.
- **Round 1:** the phone order was fixed on screen only, with CSS `order`, while Tab order still put Needs you last. ux raised it as a CHANGE, code and ui raised it as D3 and D4, and the builder had already flagged it as D2.
- **Round 2:** fixing that meant building the columns in order inside `render()`. That led the ux reviewer to the poll loop, which throws away focus every two seconds.

Each fix was right for the part it touched. The problem was the scope: the intent's Approach listed three local fixes and never named the render loop or where `aria-live` sits. Another round on the same intent would have found the next layer.

You have already changed the right thing, which was the intent rather than the code. O6 is narrowed and the remaining layer is its own bug. I see no reason for another build round on this change. Landing it as it stands, with 2026-11-17-50 carrying the rest, fits what the reviews found.

For the follow-up, two things:
- Write focus surviving a poll, and `aria-live` sitting only on the status line, into that bug's intent as outcomes in their own right.
- Accept that source-reading tests can't show focus behaviour at runtime. Both rounds showed that's where the problems are. Add a browser check later, or knowingly do without one.

- IMPACT: patch — on a phone and by keyboard, the board's page shows Needs you first, keeps Tab inside the file drawer, and labels the verifier chip; nothing anyone runs or configures changes.
