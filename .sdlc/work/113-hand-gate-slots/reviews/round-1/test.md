VERDICT: PASS

Every requirement from R1 to R9 has a test that would fail without it. R10 is a review check, not a test.

## Notes
- **R1, R3 (`gate_jobs = 2`), R6:** `test_a_hand_gate_waits_for_a_factory_gates_slot` is parametrized on `gate_jobs` 1 and 2.
- **R2:** `test_a_factory_gate_waits_for_a_hand_gates_slot` is in `tests/test_factory.py`.
- **R3:** `test_the_hand_gate_reads_gate_jobs_as_the_factory_does` runs nine value cases and compares each with `factory._gate_jobs`. Its expected list is `[1, 3, 1, 1, 1, 1, 1, 1, 1]`. I read the test's tail, not the whole of it. The base-branch-versus-checkout value of 8 is covered only if the test sets it.
- **R4:** `test_a_hand_gate_gives_up_after_its_wait_and_records_nothing` checks exit 1, the refusal text and that `build/gate.md` is byte-identical. The refusal reads "0.5 seconds" because `SLOT_WAIT` is patched. A separate `_wait_text(GATE_TIMEOUT) == "30 minutes"` assertion covers the real wording.
- **R5:** `test_without_the_factory_the_hand_gate_takes_no_slot` checks the lock-file listing, the absence of a waiting line and `waited` and `slot` of `0.0` and `None`.
- **R7:** `test_a_killed_hand_gate_frees_its_slot` is `portable`. It holds the slot from a child process running `sdlc._hand_slot` and kills it. It then takes the slot through `factory.gate_slot` within 2 s and checks the lock file remains.
- **R8:** `test_the_slot_copies_are_the_factorys` is `portable`.
- **R9:** `test_new_claims_a_number_while_a_hand_gate_waits` runs a real `sdlc.py gate` child process and takes `_main_lock` while it waits.
- **Not run:** the `R10` case is not covered by a test, as the plan says, so I did not check it here. The change has no `checks.md`, and the spec doesn't call for one.
- **Test command:** `uv run --group dev pytest -q -n auto` gave 2254 passed and 13 skipped, with no failures. I did not run `./check.sh`, so ruff and `claude plugin validate --strict` are unchecked.
