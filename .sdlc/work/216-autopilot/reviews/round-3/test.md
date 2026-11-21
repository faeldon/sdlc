VERDICT: PASS

The kept finding is fixed, and a test that can fail covers it.

- **The fix:** `main()` calls `take_markers()` first. That takes `AUTOPILOT_RUN_ENV` and `TRAIN_RUN_ENV` out of `os.environ` as `factory.py` starts. Only `loop_env()` puts them back, for the loop's own children (`run_step` and the train's `_run_env`). So the host's check, `sdlc.py accept` and the change's tests no longer see either marker.
- **The test:** `test_the_changes_own_code_never_runs_as_a_loops_child` runs `gate` and `accept` through the real `run_step` under the held lock. Both write their `env` to a file, and the test asserts neither marker is in it. It would fail without the fix, because `run_step` sets the marker.
- **Agent sessions:** `test_an_agent_session_never_carries_the_loops_markers` and `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` cover this. The second one runs a real `run_step` for `answer --by autopilot`: refused without the lock, accepted under the loop's env, refused again with `agent_env()`.
- **Status:** `test_candidates_come_from_the_real_status_json` calls the real `sdlc.py`, with no stub.

## Notes
- The gate record `build/round-3.gate.md` is green: 3935 passed, 29 skipped.
- I ran `tests/test_autopilot.py::test_the_changes_own_code_never_runs_as_a_loops_child` and `tests/test_autopilot.py::test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does`; both passed (2 passed).
- I did not read `checks.md`, and nothing was run from it.
