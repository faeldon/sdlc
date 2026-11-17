VERDICT: PASS

## Notes

**Requirements walked:**
- R1 is covered by `_hand_slot` wired into `cmd_gate`, and `test_a_hand_gate_waits_for_a_factory_gates_slot` (both `gate_jobs` 1 and 2) checks it.
- R2 is covered by `test_a_factory_gate_waits_for_a_hand_gates_slot`.
- R3 is covered by `_gate_jobs_at` and the nine-value comparison test against `factory._gate_jobs`. The checkout's `8` is set in every case.
- R4 is covered. The give-up returns `_refused` before any record is read or written, and the test compares `gate.md` byte for byte.
- R5 is covered. The test checks that no lock file appears.
- R6 is covered. `Seconds:` times only the check, and `waited` and `slot` are in the JSON summary.
- R7 is covered. The `_hand_slot` `finally` closes every descriptor, which frees the OS lock.
- R8 is covered by `test_the_slot_copies_are_the_factorys`, which pins the constants. The lock functions are pinned by behaviour through the cross-script holds.
- R9 is covered. `_hand_slot` takes neither `_main_lock` nor `sdlc.lock`, and the test claims `_main_lock` while a gate waits.
- R10 is covered by `docs/REFERENCE.md`, `plugins/factory/README.md` and the `factory.py` docstring and comment, plus the AGENTS.md factory-paragraph edit the person approved.

**Done well:**
- The cross-implementation tests hold a slot with one script's code and gate with the other's, so a drift in the lock file name or locked byte would fail a test.
- Hashing the build and the `after` digests now happen inside the slot, so the build judged is the tree as it stands when the check starts.
- `_unlock` was reused rather than copied. On POSIX it is a no-op (close releases the flock), and on Windows it is the same `msvcrt` unlock at offset 0.

**Nits / optional:**
- `_hand_slot` prints "(N of N in use)" even though, by definition, all slots are in use. This matches the factory's own line, so it is consistent.
- `_try_lock` is a near-duplicate of the factory's. That is by design (pinned copy), and it is pinned by behaviour only.
- The `os.open` loop could leave descriptors open on an `OSError` midway. The `finally` closes `fds`, so it is fine.

**Ran:**
- `uv run --group dev pytest -q -n auto`: 2254 passed, 13 skipped.
- The hand-gate slot tests alone: 8 passed.
- `ruff check`: clean.
- `ruff format --check`: clean.
- I did not run `claude plugin validate --strict` or `./check.sh` as a whole.
