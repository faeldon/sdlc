VERDICT: PASS

The gate record for round 1 is green (`build/round-1.gate.md`). I ran no tests myself. My review rests on reading the diff and the new tests.

## Notes

- NIT: plugins/factory/scripts/factory.py:1586: a read that printed output and then hits a blank line and a `## Notes` heading with no `exit:` keeps the section open. Any later `$ ` line in that report is then counted as an evidence command. This is a deliberate trade-off and the docstring says so, but a test pinning that case would make it explicit. {tests S low}
- Done well:
  - Each part of the change has a test. The `read_evidence()` tests cover 189's report shape, the commands after it, a heading after an `exit:`, and a silent read.
  - `test_train.py` runs a modify/delete conflict through a whole train for both `UD` and `DU`, and the second test checks that a stray edit outside the moved files is still refused.
  - The fence stays script-decided. Only the files the deleting commit added or changed pass `--continue`, and the marker names them for the re-review.
  - Both nits (2026-11-20-8 and 2026-11-20-9) are fixed, and `GREP_FOLLOWS_MIN` replaces the off-by-two length check.
- Tests run: none. I read the gate record and the diff only.
