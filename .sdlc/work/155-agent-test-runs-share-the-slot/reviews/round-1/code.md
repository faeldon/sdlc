VERDICT: PASS

No Critical or Required findings. I reviewed round 1 by reading the diff, the spec and the gate record. The gate record is `build/round-1.gate.md`: GATE: PASS, 2867 passed. I ran no tests myself.

## Notes
- **Requirements:** R1–R12 each have code and a test or a doc edit.
  - `cmd_check()` and the shared `_run_check()` cover R1–R5.
  - `check_line()` is appended to the builder's and resolver's prompts only (R6).
  - The prompt edits are covered by `test_skills.py` (R7–R9).
  - `FACTORY_CHECK_RE` is added to `metrics.py` (R11), with cases for `check`, `land-check` and `gate`.
  - The `AGENTS.md` and README edits and the `factory.py` docstring cover R12.
- **R10 test location:** the test is `test_evidence_citing_the_gate_record_is_a_read` in `tests/test_factory.py`, not `tests/test_evidence.py` as the spec says. The builder's `plan.md` records this difference.
- **Landing prompts:** the builder's landing prompts (`resolve`, `land-fix`) also name `check`, beyond R6's list. The builder raised this as a `[default]` decision and it is reasonable.
- **Done well:**
  - One runner (`_run_check()`) keeps a single place where `factory.py` runs the host's command, and `gate`'s capture and record are untouched.
  - `check` writes no record and never clears the gate.
  - The tests for slot sharing, timeout and slot release when `check` is killed cover the contention this change is meant to remove.
- NIT: plugins/factory/README.md:170: the rewrapped "One gate at a time" bullet leaves one line over the wrap width {style S low}
- NIT: scripts/metrics.py:132: `FACTORY_CHECK_RE` accepts an optional quote after `.py`, so a quoted path matches, which the test covers. The same quote case isn't handled for `HAND_GATE_RE`, so the two regexes treat quoted paths differently {robustness S low}
