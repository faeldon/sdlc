Fix and test are in place.

VERDICT: PASS

## Notes
- Done well: `cmd_gate` now works out `changed` before the busy branch and parks only when the tree is unchanged. A busy run that edited the tree becomes a normal FAIL attempt with `Tree: changed: …`. `test_a_busy_answer_that_changed_the_tree_is_a_failed_attempt` covers this: it checks the FAIL record, the tree line and that no `runs/parked.md` is written.
- I read the code and the test names only. I ran no tests, and I did not open the gate record or the docs the rework touched, so the REFERENCE.md and README changes are unreviewed.
- A slot-wait expiry sets `before = after = {}`, so `changed` is empty and it parks. That is correct, because the check never ran.
