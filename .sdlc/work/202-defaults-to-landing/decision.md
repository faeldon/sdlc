DECISION: READY

**Why:** All 12 requirements are built, and the test reviewer found a test for each one. Most of those tests failed before their code went in; the R6, R7 and R9 pins were shown to fail against a deliberately broken copy of the code. All four round-1 reviewers (code, security, test, behaviour) gave `VERDICT: PASS`. The gate is green: `./check.sh` exited 0, with 3561 passed and 29 skipped. Each place the build departs from the spec is written into `plan.md`, and no review suggests the spec itself was wrong.

**Open items**
- None. The three findings are nits, all recorded in `findings.md` (F1 from code, F2 from security, F3 from test). None of them asks for a change.

**Decisions to confirm**
- None. There is no `decisions.md`, and the prompt names no open default.

**For the person at ship**
- **Look at these first in the diff:**
  - `plugins/factory/scripts/run_state.py`: `uncarried()` and how `loop_state()` registers its problem under `mendable["approver"]`. This is the check that keeps a READY from leaning on a default it isn't allowed to carry.
  - `plugins/factory/scripts/landing.py`: `land_parts()` and `land_shown()`. This file is in this repo's `[review] sensitive`. `land_signals()` and `_dispose()` are unchanged, which is why `by=auto` stays refused for any carried default.
- **One hardening point to weigh (F2):** `intent_closes()` reads `closes:` from the change's own branch, while the sensitive-path bar comes from the base branch. If a build removed `closes:`, it would skip the `/sdlc-factory:decide` stop, but not your landing question.
- **Published interfaces this changes, all approved in the spec's *Contracts touched*:**
  - The approver's new `- CONFIRM: D<n>:` line.
  - The new `confirm` field in `ask`'s items.
  - The new list entry in AGENTS.md's *The factory* paragraph of stops a run mends. The spec calls this out for your approval as `[Policy text changes] The one stop a run mends`.
- **Not exercised in a live factory run:** the behaviour reviewer didn't run the spec's check by hand (`verdicts`, `status`, `land-check` on a scratch change). It relied on the gate and the targeted tests.

- IMPACT: minor — The factory approver can now carry an assumed default to the landing with a `CONFIRM` line, so a change whose only open calls are defaults no longer stops at `/sdlc-factory:decide`. `ask` also gains a `confirm` field. Nothing someone already uses has to change.

**Each undone item's disposition**
- None: there is no `notes.md`, and the builder reports nothing left in it.
