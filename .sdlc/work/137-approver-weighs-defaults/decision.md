DECISION: ESCALATE

**Why.** I'm escalating only because D1 and D2 in `decisions.md` are still unticked, so the build rests on two defaults you haven't confirmed. The build itself looks done. All four reviewers (code, test, ui, ux) gave `VERDICT: PASS` in round 2. Every requirement R1–R17 has code and a test that fails without it, by the test reviewer's account. The round-2 gate passed (`./check.sh`: 2457 passed, 17 skipped).

**Open items**
- None. Round 1 kept three ux changes (C1, C2, C3), and round 2's ux and code reviewers confirmed all three are fixed.
- The one remaining finding is F1, a code-review nit, already recorded in `findings.md`. On a blocking line, picking the recommendation is written as a non-`KEPT` answer, so `ask --answered` says `rebuild`.

**Decisions to confirm**
- D1: the build assumed that a default the approver settled keeps a batch from landing by itself (spec R9). The alternative is no signal: a READY batch whose only open items the approver settled would land `by=auto`. That moves O6 further, but an agent's call would reach `main` without you seeing it. The spec writer left this question for you, and this choice sets how much this change actually cuts escalations at the landing.
- D2: the build assumed the fix that stops the landing listing and signalling a superseded default as "assumed" stays in this change rather than being split out (R8's `open` check). This slightly changes the landing's signals for existing ledgers.

**For the person at ship**
- **Check `cmd_decisions()` in `plugins/factory/scripts/factory.py` first.** It ticks `→ settled by the approver:` and fills a bare line's options once. Make sure no path writes `→ decided:` for the approver. The landing side is `land_parts()`, `land_signals()` and `land_shown()`.
- **The ledger has no options under D1 and D2.** Both build reports gave them `OPTION`/`WHY` sub-lines, and the round-2 re-raise was meant to fill them in (R3). This ledger was most likely written by the installed factory, which doesn't have this change's code yet. Even so, it's worth checking by hand with step 1 of the spec's Verification against the change's own `factory.py`. That run should also show `settled`, `unsettled` and `bare` in the JSON.
- **The copied parsing.** `FACTORY_SETTLED` in `scripts/sdlc.py` and `SETTLED` in `scripts/board.py` should be pinned against `factory.py`. `decide_step()` is shared by status and the board.
- **The skill file.** In `plugins/factory/skills/decide/SKILL.md`, no `Edit` should come before its one WAIT. Line 77 is where F1's blocking-line case sits.
- **Agreement with 136 is still unchecked.** If 136 reads escalations by `Decisions to confirm`, whichever of the two lands second should switch it to the `- ESCALATED: D<n>:` lines.

- IMPACT: minor — someone on the previous release gains a new `/sdlc-factory:decide NNN` skill, a read-only `factory.py ask` command, defaults the approver can settle with their alternatives in the ledger, and a new `defaults_settled` key in `Sdlc-Rework`. Older ledgers and trailers still read as before.

There's no `notes.md`, so there are no unfinished items to carry forward. The prompt names no irreversible paths, so there's nothing to recover.
