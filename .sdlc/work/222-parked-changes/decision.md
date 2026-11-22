DECISION: READY

**Why:** Round 2 is all `VERDICT: PASS`. The one finding kept from round 1 is fixed. `cmd_gate` now works out `changed` before the busy branch and parks only when `busy and not changed`. A busy check that edited the tree becomes a `FAIL` attempt with `Tree: changed: …` and no `runs/parked.md`. `test_a_busy_answer_that_changed_the_tree_is_a_failed_attempt` covers it, and the code, test and security reviewers each ran it and saw it pass. The round-2 gate (`./check.sh`) is green with 3988 passed and an unchanged tree. R18 was split as the first decision advised, so no requirement is left untestable.

**Open items**
- None. Every reviewer's round-2 verdict is PASS, and the only item in `notes.md` is ticked.

**Decisions to confirm**
- No blocking decision is unticked. D1 to D6 and R1 are all ticked: D1 and D3 were decided by the person, D2 and D4 were settled by an earlier approver, and D5 and D6 were seen. No default is open.

**For the person at ship**
- Look first at `cmd_gate` and `_gate_busy` in `plugins/factory/scripts/factory.py` (around lines 4008–4012).
  - A slot-wait expiry sets `before = after = {}`, so it still parks, which is correct because the check never ran.
  - With `--land`, a busy answer that changed the tree is now a `FAIL`. The train treats that as the gate's fault and ejects the change, rather than stopping on a `problem`. The security reviewer judged this the right call.
- Then look at `plugins/factory/scripts/autopilot.py`, which is a sensitive path.
- Last, look at the `AGENTS.md` `verdicts` sentence. It is the policy edit the approved spec's *Contracts touched* names, and D1 confirmed it.
- Read the README and `docs/REFERENCE.md` prose on `[park]`. The spec leaves its wording to the ship review, and round 2's code reviewer did not review the docs the rework touched.
- The board's `.step.parked` dashed border and the `⏸ ` word in `scripts/board.html` are checked by reading only. The screenshot fixture has no parked card.
- The published interfaces the change touches are the ones the spec names, with the person's approval at the spec stage:
  - the `[park]` config
  - `runs/parked.md`
  - the `parked` stop way
  - `factory.py park`

- IMPACT: minor — a host can now set `[park] exit` so a busy resource parks a change with a deadline and a retry, which it couldn't do before. A host without the key sees no change, except that a gate-slot wait now ends.

No unticked `- [ ]` items remain in `notes.md`, so there are no UNDONE dispositions to give.
