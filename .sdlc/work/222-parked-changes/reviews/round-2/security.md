VERDICT: PASS

The change kept last round has been made. No new Critical or High finding.

## Notes

- **The kept change is done.** In `plugins/factory/scripts/factory.py:4008-4012`, `cmd_gate` now works out `changed` from `before`/`after` before the busy branch. It returns through `_gate_busy()` only when the answer is busy and nothing changed (`if busy and not changed:`). A busy run that edited the tree goes on to `verdict = "FAIL"` and writes a normal attempt with `Tree: changed: …`. It also skips the park cleanup's `PARKED` write. So a check can no longer edit the change, exit with `[park] exit`, and leave the edit for the next attempt's `before` snapshot to absorb.
- **The slot-wait path is safe.** On a `SlotWaitExpired`, `before = after = {}`, so `changed` is empty and the code returns busy before it reaches `slot` or `waited`. Those two are never bound on that path, and they are never read.
- **A landing's gate behaves correctly too.** With `--land`, a busy answer that changed the tree is now a FAIL attempt instead of a `problem` that stops the train. That is the right call: the train treats it as the gate's fault and ejects the change, instead of landing a worktree that differs from the commit.
- **The test asked for is there.** `tests/test_factory_park.py:150`, `test_a_busy_answer_that_changed_the_tree_is_a_failed_attempt`, has a check append to `README.md` and then exit with the park code. It asserts exit `75`, `tree == "changed: README.md"`, a record starting `GATE: FAIL`, and no `runs/parked.md`. I ran it and it passed (1 passed).
- **The docs match the code.** `plugins/factory/README.md` and `docs/REFERENCE.md` both say that a busy answer from a check that changed the tree is a red attempt (`Tree: changed`), never a park.
- **What I checked.** I read the `cmd_gate` and `_gate_busy` code in the reworked `factory.py` and the round-2 gate record (`build/round-2.gate.md`, `GATE: PASS`). I ran only the one named test above, not the gate.
