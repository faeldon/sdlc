DECISION: ESCALATE

**Why:** The security reviewer's finding is still open after round 1, and the arbiter kept it. `cmd_gate` returns on a busy answer before it works out `changed`. A check that edits the tree and exits with the park code is therefore parked, and the edit is never flagged. The next attempt then reads `Tree: unchanged` and goes green, and on `--land` the gate can pass on a worktree that differs from the commit that lands. I read only the run files, not the code or tests, so this rests on the arbiter's account. The rounds also left R18 (prose wording) untestable, and D1 and D3 need the person.

**Open items**
- security: `plugins/factory/scripts/factory.py:3934`: compute `changed` before the busy branch, and set `before = after = {}` on `SlotWaitExpired`, where the check never ran. Add a test where a check edits a tracked file and exits with `[park] exit`. It should assert a FAIL attempt with `Tree: changed` and no `runs/parked.md`. Add a second test that a slot-wait expiry is still BUSY with no `Tree:` line.

**Decisions to confirm**
- ESCALATED: D1: the `AGENTS.md` edit changes a rule in the project's architecture map (policy), so I may not settle it. The builder assumed the approved spec's yes covered it. The person should confirm that, since the diff also touches a sensitive path.
- SETTLED: D2: the spec leaves the catching to the plan, and R1 requires that a host without `[park] exit` sees no change. Catching only when the key is set is the one option that meets R1 and still lets the payload be read.
- ESCALATED: D3: the builder prints the park's line in two lines, while R16's wording says one line. That departs from the spec's wording, so the person should decide it.
- SETTLED: D4: R9 fixes the form of the `parked` stop's next step, and the build follows it exactly with no `/sdlc:ship` alternative. Shipping by hand would meet the same busy check.

**Other reasons to escalate**
- ESCALATED: look: `plugins/factory/scripts/factory.py: cmd_gate()` / `_gate_busy()` — a Critical or High security finding (the park path hides tree changes) is still open and needs a fix, unless the person accepts it.
- ESCALATED: look: `REFERENCE.md` and README prose on parked changes — R18 can't be tested, so a person must read the wording.

## Reconsider the approach
Round 1 is the only round so far, and it didn't run out of rounds. The run stopped because the builder reported R18 as untestable. The next step is to rewrite R18. Split it into a testable part and a part a person reads:
- The testable part: the feature-map entry and the states table exist, which tests already cover.
- The person-read part: the prose wording, taken off the requirement list and left to the ship review.

Separately, the builder should fix the security finding above. The park path should treat a busy answer as busy only when the tree is unchanged.

**For the person at ship:** look first at `cmd_gate`/`_gate_busy` in `factory.py`, then the `[park] exit` handling in `plugins/factory/scripts/autopilot.py` (a sensitive path), then the `AGENTS.md` `verdicts` sentence. No published interface is touched beyond what the spec names.

- IMPACT: minor — a host can now set `[park] exit` to park a change on a busy resource and retry later, a capability it didn't have before.

- UNDONE: security: plugins/factory/scripts/factory.py:3934: `cmd_gate` returns through `_gate_busy()` (`if busy: return _gate_busy(...)`) before it works out `changed` from `before`/`after`. So a busy run that changes the worktree is never seen. A gate's "Tree: changed → FAIL" rule exists to catch a check, running code the builder wrote, that rewrites the change it is judging. On a host that sets `[park] exit`, that code can now edit files, exit with the park code (for example `os._exit(75)` from a test), and leave the edit behind. The next attempt's `before` already holds the edit, so it reads `Tree: unchanged` and goes green, with `Build:` still the hash of the snapshot taken before the edit. Later rounds' reviewers read only `reworked`, worked out from those snapshots, so an edit on a path the rework didn't touch never reaches a reviewer. On `--land`, the gate goes green on a worktree that differs from the commit that lands. Fix: compute `changed` before the busy branch, and treat a busy answer as busy only when nothing changed (`busy = None if changed else busy`). A busy run that changed the tree then becomes a normal `FAIL` attempt with `Tree: changed: …`. Add a test where a check edits a tracked file and exits with `[park] exit`, asserting a FAIL attempt is written and no `runs/parked.md`. → dropped: the builder is sent back to fix it in this change (it is the kept finding above), so it is done after the rebuild and needs no seed.
