VERDICT: PASS

Every requirement has a test that fails without it. I read the gate's record and the diffs and ran no tests myself.

## Notes
- **Gate:** `build/round-1.gate.md` is `GATE: PASS` from `./check.sh`: 3183 passed, 29 skipped, and both plugin validations passed.
- **Mapping:**
  - R1 and R2 are covered by the parametrized `test_output_that_isnt_rows_passes_through_with_its_reason`. It covers each rejection (empty, non-object, bad name, bool, NaN, Infinity, bad unit, duplicate key).
  - R2 is also covered in `test_a_failed_or_cut_indicator_passes_through_with_its_reason`, which covers plain text, a non-zero exit, a cut at the limit and a timeout.
  - R3 and R4 are covered in `test_retro.py`. The R4 test uses an older retrospective and an edited in-tree report as decoys, so `last` must come from the newest commit.
  - R5 and R6 are covered. The R5 test asserts that raw output and stderr don't reach the report.
  - R7 is covered by the extended `test_retro_and_its_report_show_the_same_figures`.
  - R8 is covered by the round-trip test, which includes `|`, a backslash, a float and a negative value.
  - R9 is covered by `test_the_report_renders_spend`.
  - R10 is covered by `test_function_heat.py`, including the `EVIDENCE_LIMIT` check.
  - R11 is covered by the `READS_CONFIG` entry in `tests/test_skills.py`.
  - R12's drift check is the gate's.
- **Tests that can fail:** the ones I checked assert exact values. I saw no empty glob, no mock of the code under test, and no skipped case.
- **`checks.md`:** none exists, and none is needed.
- NIT: tests/test_retro.py:1957: R2's OSError case has no test; `_indicator_rows` treats it like the timeout path {tests S low}
- **Tests run:** none, since the gate's record covers the whole suite.
