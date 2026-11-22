DECISION: READY

**Why:** The intent's outcomes are built and tested, and the code reviewer says so. The gate is green (`./check.sh`: 4036 passed). All four round-1 reviews are `VERDICT: PASS`, with no `CHANGE` findings and only two low NITs. Nothing in the reviews suggests the spec was wrong. I read the gate record, the code review's account and the verdict lines. I did not read the diff.

**Open items:** None. The two NITs (the `needs_of()` docstring wrap, a comment for the board's stale `mend` step) are style only.

**Decisions to confirm:**
- CONFIRM: D1: The build uses the agent's own timeout (`AGENT_TIMEOUT`, 3 hours) as the point where an unmended `mend` stop becomes the person's. A shorter figure would surface a dead mend sooner. The cost is bounded, because the card waits at most 3 hours if a supervisor crashes. It is a threshold, not scope, policy or a published interface, so the person's yes at the landing is enough.
- SETTLED: D2: The intent's Approach already names `runs/step.md` with `STEP: mend`, and the code reviewer confirmed the diff follows it. The new `ROLE:` line is optional, so the step record gains nothing a reader must have. The alternative, `runs/mended`, is only written after the reply, so it would fail the intent's outcome that the card changes when the supervisor acts.

**For the person at ship:**
- Look first at `needs_of()` in `scripts/sdlc.py` and `mend_running()`, which decides "mending" against "Needs you".
- Then look at `agent --task mend` in `plugins/factory/scripts/factory.py` and its failed-mend restore, `_unrecord_mend`.
- Last, the board's mending step in `scripts/board.py`, and the `factory_records.py` copies pinned by `tests/test_modules.py`.
- No published interface the person hasn't approved is touched. `needs_of()` stays the one place needs are decided, as the intent's Contracts say.

- IMPACT: patch — a mend under way now shows as "mending" on the board and in `status` instead of "Needs you"; nothing anyone must do differently.

**Undone items:** `notes.md` has no unticked `- [ ]` items.
