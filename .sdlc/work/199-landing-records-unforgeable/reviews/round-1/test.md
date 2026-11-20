VERDICT: PASS

Every requirement from R1 to R10 has a test that would fail without it, and I found no test that can't fail.

## Notes

- **Gate record:** `build/round-1.gate.md` is green: 3556 passed, 29 skipped, and `claude plugin validate --strict` passed. I ran only `tests/test_records_ledger.py` myself: 6 passed.
- **R1:** `test_gate_vouches_for_its_record` (`factory.py gate`), `test_accept_vouches_for_its_record_and_refuses_one_it_didnt_write` in `test_land.py` (`factory.py accept`) and `test_the_hand_gate_vouches_for_its_record` (`sdlc.py gate`). Each compares the ledger rows to the file's hash.
- **R2:** `test_vouched_reads_the_ledger_alone` covers a one-byte change and its restore, another change's folder, another record path, a garbled line and a missing ledger. `test_a_crlf_record_stays_vouched` is marked `portable`.
- **R3:** `test_land_refuses_a_hand_written_record`, parametrized over `accept` and `round gate`. It asserts `state: refused`, the file named, the branch HEAD unmoved and no stage change.
- **R4:** `test_land_verdict_stops_on_a_hand_written_record` is the only R4 test; it covers an unvouched land gate or accept record, settled or not.
- **R5:** `test_train_run_stops_on_a_hand_written_record`, parametrized over the gate and build records. It asserts nothing closed and no attempt in `state["gates"]`.
- **R6:** `test_a_hand_written_hand_gate_clears_nothing` also checks that a genuine gate does clear.
- **R7:** each of the three writers has a test that plants a forged attempt. They assert the refusal, that the file is unchanged, that the marker command never ran and that the ledger is empty. The factory gate test also checks the run goes ahead once the file is removed.
- **R8:** `test_the_ledger_writer_is_pinned_to_core` pins the constants, the digest and the line, and both writers' appended lines are equal.
- **R9:** `test_two_writers_at_once_leave_whole_lines` runs two processes of 200 appends each and checks all 400 rows.
- **`checks.md`:** the one check greps the docs for the ledger's name and the stated limit. I read its `sh` block and ran the same greps by hand to see whether they pass; they exit 0 on the tree as it stands. It would fail only if those doc sentences were removed, and it leaves the tree unchanged, so it is a sound acceptance check for R10.
- NIT: tests/test_records_ledger.py:152: the writer test runs 400 locked appends across two processes, which may be slow on a loaded machine; a smaller count would still prove whole lines {tests S low}
