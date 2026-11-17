I've read every round, the decisions ledger and notes, and compared the page with `main`'s copy. Here is the recommendation.

DECISION: ESCALATE

**Why.** The rounds ran out with one change still open. In round 2 the ux reviewer found that the board rebuilds every card on every 2-second poll, and the verifier kept it twice. That means a keyboard user loses focus before they can open a card, which is exactly what this change is meant to fix. The rest of the intent is built, tested and reviewed: phone order, the drawer's focus trap and the chip's label all pass, and the gate passes with 2001 tests. All four decisions in `decisions.md` are still unticked.

**Open items**
- ux (round 2, kept by the verifier): `scripts/board.html:293`. The render key is `JSON.stringify([NARROW.matches, st.changes])`, and `touched_ago` is in whole seconds (`board.py:161`). So every poll rebuilds every card, and focus drops to `body`. Because `#board` is `aria-live="polite"`, a screen reader may also re-read the whole board each poll. The suggested fix: key on what is shown (the `ago()` text), move `aria-live` to `#status`, and add a test that pins the key.
- Not this change's fault: `main`'s `board.html` already has `key = JSON.stringify(st.changes)` and `aria-live` on `#board`. This change only added `NARROW.matches` to the key. The problem predates the change, but it still stops the outcome "the board reads the same … by keyboard and with a screen reader" from being true.
- Still open in `notes.md`: nothing runs the drawer's trap in a browser. The tests only read the page's source.

**Decisions to confirm**
- D1: the chip's label is visible text, `verifier: kept N · dropped M`, rather than an accessible-only label.
- D2: phone order by CSS `order` alone. **The build no longer does this.** Round 2 removed the CSS rule and orders the columns in the page itself (`columnOrder()`), so this default no longer matches the build.
- D3 (code) and D4 (ui): both recommended ordering the columns in the page with `matchMedia`, which round 2 built. Tick both as decided that way, and record D2 as replaced by them.

**For the person at ship**
1. Look at `render()` and its key at `board.html:293`, next to `board.py:161`. Decide whether fixing the per-poll rebuild belongs in this change or in a follow-up.
2. Then `columnOrder()` and the `NARROW` listener (`board.html:164-172` and `:385`), which replaced the CSS `order` rule.
3. Then the drawer's keydown and trap handler, and the `.doc` pane's new `tabindex` and label.

## Reconsider the approach

The same problem came back in both rounds: what a keyboard or screen-reader user actually gets was not what the code and screenshots seemed to show.
- **Round 1:** phone order was fixed on screen only (CSS `order`), while Tab order still put Needs you last. Three reviewers raised it (ux as a CHANGE, code and ui as D3 and D4), and the builder had already flagged it as D2.
- **Round 2:** the fix rebuilt columns through `render()`, which pointed the reviewers at the poll loop that throws away focus every two seconds.

Each time, the code was right for the part it touched, and the gap was one layer further out. **The intent and its Approach are what should change, more than the code.** The Approach scoped the work as three local fixes (a CSS rule, a keydown handler, a label) and named "a media-query `order`" as the method. But reaching the page by keyboard and screen reader depends on the render loop and on where `aria-live` sits, and the intent never listed either.

Another build round on the same intent would likely turn up the next layer out. The person should pick one:
- **(a)** Widen the intent: make "focus survives a poll" and "`aria-live` only on the status line" outcomes in their own right, then rebuild with those in scope.
- **(b)** Land this change for what it does fix, after reworking the intent's O6 line so it no longer claims the board fully works by keyboard and with a screen reader. Then file the render key and `aria-live` as a new `[bug]` seed.

On either path, the source-reading tests can't show runtime focus behaviour. `notes.md` already says so, and both rounds showed it is where the problems hide. Whether to accept that, or add a browser check later, is the person's call.

- IMPACT: patch — the board's page behaves better on a phone, by keyboard and in its chip's label; nothing anyone runs or configures changes.
