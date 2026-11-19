VERDICT: PASS

The landing resolution is sound. The one conflicted file, `scripts/retro.py`, keeps both sides in `render_report`'s signature (`cost`, then `indicators`) and in `retro_report`. The call `render_report(template, process, spend, value, metrics, cost, host)` matches the signature.

## Notes
- **Gate record:** `build/land-1.gate.md` does not exist in the change folder. I read `build/round-2.gate.md`, green per the round-2 review, as the last record, and did not run the whole suite.
- **Named tests I ran in the foreground:** `tests/test_indicators.py`, `tests/test_retro.py` and `tests/test_function_heat.py` together: 264 passed. This is not the whole suite.
- **Tests covering both sides of the merge:** the landing builder reported 189 passed in `tests/test_retro.py`; my run of the three files agrees. The tests that cover the R1–R10 requirements and the cost pass were already in `tests/test_retro.py`. The merge changed only `retro.py` signatures, and those tests exercise the combined path.
- **`render_report` call sites:** the existing tests that call `render_report` positionally or by keyword (`indicators=host`) still pass against the merged signature.
- **Well covered:** the R1/R2 reasons, including the overflow case from round 2, the R8 round trip, the R7 split between indicator and evidence commands, and the R9 template-reads check.
- **`checks.md`:** the change has none, and no requirement needs one.
