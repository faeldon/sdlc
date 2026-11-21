VERDICT: PASS

## Notes
- The rework in `tests/test_ci.py` reads both `.yml` and `.yaml` workflows. A fixture test covers that, and the real-workflow test asserts at least one workflow exists, so it can't pass on an empty folder.
- The matcher test has negative cases for a tag, a branch, a short SHA and a SHA with no version comment. It also skips local `./` actions.
- I ran `tests/test_ci.py`: 3 passed. I didn't run the gate.
- NIT: tests/test_ci.py:15: `USES` still misses a quoted `uses: "a/b@v4"` {robustness S low}
