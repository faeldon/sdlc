VERDICT: PASS

## Notes

**Scope.** In round 2 the rework changed only `tests/test_train.py`. I reviewed that path, and I checked the change kept from round 1.

**The kept change was made.** At `tests/test_train.py:1770`, `test_a_killed_train_run_resumes` now waits on a 120 s `time.monotonic()` deadline and polls every 0.05 s. Before, it looped 600 × 0.2 s. This is what the kept change asked for. The new shared helper `_killed_at_its_gate` uses the same 120 s deadline and 0.05 s poll, so the POSIX and Windows gate-kill tests have the same margin. That change was a behaviour finding, not a security one. Whether 120 s is enough margin is for the behaviour pass to judge, not me.

**Trust boundaries in the reworked test code.** The test code adds no entry point for untrusted data.
- **`BLOCKING_CHECK`:** a fixed Python source string. It is written into the test's own `tmp_path` and run as the scratch host's `[commands] check`, using `sys.executable` and quoted posix paths under `tmp_path`. No outside input reaches it.
- **`taskkill`:** the Windows kill calls it with an argument list (`/T /F /PID <pid>`), with no `shell=True`. Only an integer pid goes into it.
- **Process groups:** `start_new_session` and `CREATE_NEW_PROCESS_GROUP` keep each kill inside the test's own process tree.
- **Fake behaviour verdicts:** they are written only into the scratch repo's `reviews/land-*` folders.

**STRIDE.** The tests run under pytest's temp dirs, so they add no surface for spoofing, tampering, repudiation, disclosure or elevation. The only denial-of-service risk is a test that hangs. That is bounded: the wait has its deadline, the blocking check exits once `flag` exists, and `loop.wait(30)` caps the wait for the killed loop.

**Production code.** The rest of the diff (`factory.py`, `landing.py`, `run_state.py`) has the same files I passed in round 1, and the rework didn't touch them.

**What I checked:**
- Read the full `git diff` of `tests/test_train.py` and `build/round-2.files`.
- Read `build/round-2.gate.md`: `./check.sh` passed and exited 0 on build `271a8ffcf61fb5c4`.
- Read my round-1 `security.md`.

I didn't run the gate.
