DECISION: READY

**Why:** The intent's three outcomes are all built and checked. Ready to close cards no longer pick up the drawer button's `.close` rule, because the button's class is renamed to `d-close`. The × keeps its old rule under the new name. A new portable test fails on the original clash (`['.close']`) and passes now. All three round-1 reviewers (code, ui, ux) returned `VERDICT: PASS`, the gate passed with 1851 tests, and nothing suggests the intent was wrong.

**Open items:** None blocking. Only nits:
- code: the test skips any selector that includes `.card` or `.col`, so a column-specific `.card.<key>` rule would get past it. This matches the intent's wording.
- code: the test reads the column keys from the `{ key: "…"` text in the page, so a change to that format could shrink the key set without warning. The `{"ready","close","needs-you"}` check only guards against an empty set.
- ux: confirm that `.d-close` has the same declarations as the old `.close` rule. The code reviewer compared it against `HEAD` and says it does.
- ui/ux: no screenshot shows a card in Ready to close or the open drawer. The fix is judged from the stylesheet, not from the rendered page.
- The intent's open question (which side to rename) is answered by its own Approach but still not struck in `intent.md`.

**Decisions to confirm:** None. The change has no `decisions.md`.

**For the person at ship:**
1. In the diff of `scripts/board.html` around line 95, check that the only change is the selector going from `.close` to `.d-close`, with the same declarations. That settles the ux reviewer's question about the × looking the same.
2. If you can, open `/sdlc:dashboard` with a change in Ready to close to see one of its cards and the open drawer. No reviewer saw either.
3. Strike the answered open question in `intent.md`.

- IMPACT: patch — the board's Ready to close cards now render properly. `/state.json` and every command stay the same, so nobody on the previous release has to do anything differently.
