DECISION: ESCALATE

**Why.** All five reviewers pass round 2. The one kept change from round 1 (R10's single test that `decision.md` is never rewritten) is now `test_nothing_rewrites_decision_md`. The builder showed it failing on a planted rewrite, and `./check.sh` is green with 2750 passed. Nothing open stops this build. I escalate only because the change edits the host-facing contract, which the rules leave to you:
- `sdlc.py gate` now also gates a factory run at `stage: test`.
- The board's columns are renamed.
- The ledger has a new `look` line kind that a revert would read as garbled.
- `AGENTS.md` and `docs/REFERENCE.md` are edited to say all this.

- ESCALATED: look: this edits the published contract: `sdlc.py gate` accepts a factory run at `test`, the board's columns become Planned/Designing/Building/Ready/Landing, and `decisions.md` gains the `(approver round N, look)` kind. The spec flags the hand-gate change as "a policy edit for the person to approve". Confirm the `AGENTS.md` and `docs/REFERENCE.md` wording says what you mean.
- ESCALATED: look: the intent's open question "Does `status` group its sections by the same five states?" is still unstruck. The spec's Boundaries leave it to you, and the UX reviewer asks for it to be settled before ship. Strike it, or seed it as a follow-up.

**Open items**
- None. Round 2 is all `VERDICT: PASS`, and round 1's C1 (test reviewer) was fixed and confirmed by both the code and test reviewers.

**Decisions to confirm**
- SETTLED: D1: spec R13 gives the `Escalated` block's lines word for word (`gate: green on the build as it stands (attempt N)` / `not cleared`), and one green hand gate clears every `gate` reason at once (spec, Edge cases). Identical lines lose nothing. The round-1 code review recorded it as a spec-faithful nit only.
- SETTLED: D2: R22's wait is for a change waiting to *stack on* or *close after* another, and only a committed change can be. `_amend_record()` needs the landing's commit to amend the record into (spec, Assumptions). R23's train-of-three test passes under it, and the behaviour reviewer found it matches the spec in both rounds.

**For the person at ship**
1. The `AGENTS.md` and `docs/REFERENCE.md` hunks on the hand gate and the columns.
2. `cmd_gate()`'s new `stage: test` branch in `scripts/sdlc.py`.
3. `needs_of()`'s new needs and `read the escalation` fallback.
4. `factory.py`'s copy of the hand-gate currency rule (`hand_gate_state()`, `gate_reasons()`) and its pinning test.
5. `_train_waits()`, to check where a `wait` record is and isn't written.

- IMPACT: minor — a person can now clear an escalation by acknowledging it in `decide` or by a green `sdlc.py gate`, without a rebuild. The board gains landing progress and states that are the same for hand and factory changes. Nothing anyone already does stops working.

**Undone items**
- None. The change has no `notes.md`, and the builder reports nothing new for it.

**How to recover**
- The prompt names no irreversible paths. `plan.md`'s Rollback is `git revert`, then tick or delete any `look` ledger lines by hand.
