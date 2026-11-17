VERDICT: PASS

## Notes

**Landing round:** I reviewed the whole diff against `main` as it now stands. The conflict was only in `.sdlc/work/inbox.md`. That file now differs from the base's only by seed 63, which this change builds and meant to remove. Seeds 65 and 66 stay removed, as the base deleted them. No conflict markers are left. The rebase did not touch the code, so the round-1 PASS on the code still holds.

**Requirements walked against the code:**
- **R1–R3:** `cmd_gate` takes a slot through `_hand_slot` only when `factory_enabled(home)[0]` is true. `_gate_jobs_at` reads `refs/heads/<trunk>:.sdlc/factory.toml` and applies the factory's checks (int, not bool, ≥ 1, otherwise the default). `test_the_hand_gate_reads_gate_jobs_as_the_factory_does` compares it with `factory._gate_jobs` over nine base-branch values, with `gate_jobs = 8` set on the checkout in each.
- **R4:** `SlotTimeout` is caught around the `with` block, and `_refused` returns before the record is read or written. The test compares `gate.md` byte for byte.
- **R5–R6:** With no factory it uses `nullcontext((None, 0.0))`. `Seconds:` times the check alone, inside the slot, and the JSON gains `waited` and `slot`.
- **R7:** `_hand_slot` closes every descriptor in `finally`, so the OS frees the lock when the gate dies. The test is `portable`.
- **R8:** `test_the_slot_copies_are_the_factorys` pins the constants. The lock functions are pinned by behaviour through the cross-script hold tests.
- **R9:** `_hand_slot` takes neither `_main_lock` nor `sdlc.lock`. The test claims `_main_lock` while a hand gate waits.
- **R10:** The docs say it in `REFERENCE.md`, the factory `README.md` (two places), the `factory.py` docstring and comment, and the AGENTS.md factory paragraph.

**Done well:**
- Cross-implementation tests hold a slot with one script's code and gate with the other's, so drift in the lock file name or the locked byte fails a test.
- The build hash and the `after` digests are now taken inside the slot, so the judged tree is the one the check actually ran on.

**Nits:**
- The `(N of N in use)` text matches the factory's own wording, so it is consistent.
- `HOLD_HAND` is defined in both `tests/test_factory.py` and `tests/test_hand_gate.py`. This is harmless, but could be shared.

**Ran:** I ran no commands. I relied on the builder's `build/land-1.md`, which reports `./check.sh` green after the rebase: 2257 passed, 13 skipped, `claude plugin validate --strict` passing. I read the diff and the tests myself.
