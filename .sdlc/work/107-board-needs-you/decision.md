DECISION: READY

**Why.** All three reviewers (code, ui, ux) passed in round 2. The one finding kept from round 1 is fixed. In `render()`, a local `const open` hid the drawer's `open`, so the page threw a ReferenceError whenever a card had keyboard focus. The local is now `openCount`, and `test_a_rebuild_puts_focus_back` fails if any `open` is declared inside `render()`. The builder ran that test against the old code and saw it fail. The builder's account covers R1–R16, with a named test for each of R1–R15; R16 is docs only. `./check.sh` is green on the build as it stands: 2091 passed, `round-2.gate.md`. There is no `decisions.md`. The build follows `plan.md`'s five slices, and no review suggests the spec was wrong.

**Open items**
- No CHANGE is still open after round 2.
- Not blocking (ux, round 1): answered cards still show the grey `ESCALATE` chip beside the `escalated: answered` badge, so they can look like an open escalation.
- Not blocking (ui and ux, round 1): on card 100, "the approver escalated it to you" sits right above "needs you: read the escalation" and says nearly the same thing.
- Not blocking (ux, round 2): empty columns take a full row on a phone.

**Decisions to confirm**
- None. No `decisions.md` exists; the agents raised no decisions.

**For the person at ship**
- **Start with `render()` in `scripts/board.html`.** Check the `held && !open` focus check, `openCount` and the `shownAs` replacer that builds the render key. Round 1's bug was here. The new test only reads the source text. The builder's node run against a stand-in page is the only behavioural check, and it isn't in the suite.
- **Then `needs_of()` and `answered()` in `scripts/sdlc.py`.** They are the one set of rules that picks a card's column. Check them against R4 and R5: an empty ledger must give `read the escalation`, and an escalation with a Reconsider section must never count as answered.
- **One gap against the spec, written in `notes.md`.** R2 says an unreadable stop record needs `stopped: read runs/stopped.md`. The board instead shows it as a `fix: runs/stopped.md …` problem, as 086 pinned. So for that one case the board and `■ What needs me` word it differently, while R11 asks them to agree. Both still put the change in front of you.
- **One change the spec didn't ask for.** The builder hides the "approver escalated it to you" flag once an escalation is answered. R10 keeps that flag on Needs you cards, and answered cards leave that column, so it is consistent, but confirm you agree.
- **Two hand checks no one has done in a browser yet:** Tab onto a card and confirm focus stays through several polls, and confirm VoiceOver says nothing between polls.

- IMPACT: minor — the board and `/sdlc:status` now say what each change needs, `status` gains a `■ What needs me` section and new record keys, and answered escalations move to Ready to ship; it also fixes a poll taking focus and re-announcing the board.

- UNDONE: A stop record that won't read reads differently in the two places: the board makes it a problem (`fix: runs/stopped.md doesn't open …`, card `stopped: None`, as 086 pinned), while `status`'s `factory_stop()` keeps it a stop (`stopped: read runs/stopped.md`). Both put it in front of the person; aligning them means changing one of the two pinned behaviours. → seed: Make the board and status read an unreadable stop record the same way
- UNDONE: `next_action()` is unchanged, as the spec says: an escalation that still needs `decide D2` names `/sdlc:ship, or /sdlc-factory:land …` as its next step, beside its `needs you:` line. A next step that follows the needs would read better. → seed: Make the board's next step follow what the change needs

There are no `RECOVER` lines because the prompt names no irreversible paths. If one were needed, `plan.md`'s Rollback is a plain `git revert`, since the board and `status` write nothing.
