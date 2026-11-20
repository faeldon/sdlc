DECISION: READY

**Why:** The one requirement is built. `.sdlc/SDLC.md:83` now answers the guide's `### The release loop` slot: this repo releases once each wave has landed, before the next retrospective. It doesn't restate the guide's Release due rule. Both round-1 reviewers gave `VERDICT: PASS`, the gate is `GATE: PASS` on `./check.sh` (3540 passed, which covers `tests/test_defaults.py`), and the acceptance check in `checks.md` failed before the edit and passes after it. Nothing in the reviews suggests the intent was wrong.

**Open items**
- None. The only finding, F1 (a nit from `code`), is recorded in `findings.md` and not open.

**Decisions to confirm**
- None. There is no `decisions.md`, the builder raised no decisions, and the prompt names no open default.

**For the person at ship**
- Look first at the 7-line block at `.sdlc/SDLC.md:83–88`. It's the whole diff. Check that it says what you meant by "finish the wave before releasing".
- Weigh F1 while reading: the block doesn't say what to do if a wave stalls past `status`'s 14-day Release due. One clause would settle it if you want one, but it isn't needed to land.
- The change touches no published interface, secret or destructive operation.

- IMPACT: none — only this repo's own process doc changed, and nothing a plugin user installs or runs is different.

**Each undone item's disposition**
- None. The change has no `notes.md`, so there are no unticked items.
