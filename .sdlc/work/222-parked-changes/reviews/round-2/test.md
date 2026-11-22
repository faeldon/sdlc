VERDICT: PASS

The kept change was made. `cmd_gate` now works out `changed` before the busy branch, and only parks when `changed` is empty (`factory.py:4011`). A busy answer that changed the tree becomes a normal FAIL attempt with `Tree: changed: …`.

The new test, `test_a_busy_answer_that_changed_the_tree_is_a_failed_attempt`, covers that case:
- The check appends to `README.md` and exits with the park code, 75.
- The test asserts a FAIL verdict, `tree == "changed: README.md"`, a `GATE: FAIL` record whose attempt says `Tree: changed: README.md`, and no `runs/parked.md`.
- It fails without the fix, because a busy answer returned through `_gate_busy` before `changed` was ever computed, so the edit would never have been seen.

## Notes
- The gate's record, `build/round-2.gate.md`, is green and shows `Tree: unchanged`. I did not rerun the suite.
- I ran one named test in the foreground: `uv run --group dev pytest tests/test_factory_park.py -q -k changed_the_tree`, which gave 1 passed and 21 deselected.
- The slot-wait path sets `before = after = {}`, so `changed` is empty there and it still parks. That is correct, because the check never ran.
- There is no `checks.md` to review.
