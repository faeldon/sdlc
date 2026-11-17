DECISION: ESCALATE

**Why.** The build is done and reviewed: round 2 passed all three reviewers (code, ui, ux), the gate is green with 1905 tests, and every case the intent asked for is pinned in `tests/test_board.py`. I'm escalating because all four decisions in `decisions.md` are still unticked, so the build rests on defaults you haven't confirmed. Two of them disagree with each other: D2 says no badge on a shipped escalated card, D4 says keep a `was ESCALATE` badge, and the build follows D4. Separately, `checks.md` and the three notes left open mean this change goes through `/sdlc:ship`, not `/sdlc-factory:land`, either way.

**Open items**
- No change request is still open. Round 1's code reviewer raised C1 (`next_action()` still names a stop at `test`) and C2 (the stopped flag isn't gated). The verifier dropped both, having checked in the code that a stop only reaches the board at `build` (`board.py:168`). The ux reviewer's C3 was kept and fixed in round 2.
- Round 1 code nit, not confirmed done: the new paragraph in `docs/REFERENCE.md` has a line over 100 columns, and "leaves Needs you for that stage's column" doesn't say which column. The ux reviewer raised the same wording.
- Round 1 code, optional: no test pins a pending blocking decision at `test`. If the `stage == "build"` gate moved, no test would fail.
- The builder reported this but it isn't in `notes.md`: a change moved back to `build` with an old `decision.md` still shows every step done on its step track. The column is right; the step track isn't.
- Round 2 ux, smaller: the `kept 1 · dropped 2` chip explains itself only in a tooltip (`board.html:191-198`).
- `notes.md`, three unticked pre-existing issues for ship to dispose of:
  - `next_action` shows `/sdlc:close` on a card whose file won't read.
  - At phone width, Needs you comes last in the column order.
  - The drawer has no focus trap.

**Decisions to confirm**
- D1: gate the card's flags in `board.html` too, not only `column()` and `next_action()`. The build gated them.
- D2: a shipped escalated card shows no badge. D4 contradicts this and the build didn't follow it.
- D3: a decision on a card at `build` shows no badge.
- D4: a shipped or dropped card keeps a `was ESCALATE` (or `was READY`) badge. The build follows this; to drop it, delete `board.html:255`. Settling D4 also settles D2.

**For the person at ship**
1. Look first at the ordering in `scripts/board.py` `column()` and `next_action()` (around lines 572–610). A file that won't read must come first, then `CLOSED`, then a stop or pending decision only at `build`, then the decision only at `test`.
2. Then check `scripts/board.html:249-255`: the flags and the chip must use the same stage gates as those two functions.
3. Open the board with one escalated change at `test` and one shipped. No screenshot showed a shipped or dropped card, so `was ESCALATE` has never been seen rendered.

- IMPACT: patch — the board stops keeping cards the person has already acted on under Needs you. Nothing anyone holding the previous release does changes.
