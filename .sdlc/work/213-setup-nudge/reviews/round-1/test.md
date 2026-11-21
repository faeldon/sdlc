VERDICT: PASS

Every requirement R1–R11 has a test that fails without the change, and the gate is green.

## Notes
- **Gate:** `build/round-1.gate.md` is PASS (`./check.sh`, exit 0), with 3686 passed and 29 skipped, and plugin validation passed. I ran only `test_a_doc_drift_cannot_read_keeps_the_nudge` myself, and it passed.
- **R1:** the test is built on the `set-up` fixture, so `complete` is true. It asserts `complete`, a None nudge and no `■ Setup` in status output. Today's code would return the version line there, so it fails without the change.
- **R2 and R4:** the test changes a default under the 1.1.0 record and asserts the line, then None after `_record`. It also keeps the no-record, unreadable-record and no-config cases. `test_a_current_record_runs_no_drift` swaps in a `drift` that raises, for both an equal and a newer record.
- **R3:** the report-only drift is made by removing a key from `config_keys`. The test asserts the nudge is shown and `complete` is false.
- **R6–R8:** these use a fresh cache with no release, plus the release-wins case and a raising `setup_nudge`.
- **R9–R11:** `test_check_strict_ignores_drift` now uses a stale record. The skills and REFERENCE tests assert the new prose is present.
- **Edge:** `test_a_doc_drift_cannot_read_keeps_the_nudge` can't tell whether the invalid UTF-8 makes `drift()` raise or just finds drift. Its second half, the monkeypatched `OSError`, does cover the except branch.
- **Edge:** the `ValueError` side of that branch is never raised on purpose. Raising it in the same mock would pin both exception types.
- **`checks.md`:** the change has none, and none is needed.

- NIT: tests/test_setup_lifecycle.py:735: the R5 test never forces a `ValueError`, so half of the `except (OSError, ValueError)` is unpinned; a second mock that raises `UnicodeDecodeError` would close it {tests S low}
