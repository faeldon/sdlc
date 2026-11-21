VERDICT: PASS

Each requirement I checked, and each of last round's kept changes, now has a test that would fail without it.

- **`_claude` env leak (kept change 1).** `agent_env()` removes `AUTOPILOT_RUN_ENV` and `landing.TRAIN_RUN_ENV`, and `_claude()` passes `env=agent_env()` at factory.py:4303.
  - `test_an_agent_session_never_carries_the_loops_markers` stubs `subprocess.run` and runs `cmd_agent` under the lock. It asserts the session's env has neither marker and keeps other variables.
  - It would fail if `_claude` dropped `env=`.
- **Real `run_step` path (kept change 2).** `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs `answer --by autopilot` as real subprocesses.
  - Without the lock it is refused, and with `run_step` under the held lock it succeeds and the ledger shows `decided_by: autopilot`.
  - A child given `agent_env()` is refused.
- **`status --json` (kept change 4).** `sdlc.py` now has `--json` at line 10831, and `test_candidates_come_from_the_real_status_json` calls the real `sdlc.py` with no stand-in.
- **Security finding.** It had the same cause as kept change 1 and is fixed by the same change.

## Notes
- Gate record `build/round-2.gate.md`: green, `3934 passed, 29 skipped`.
- I ran `tests/test_autopilot.py -k "real_step or real_status or agent"` in the foreground: 4 passed.
- There is no `checks.md` section to review.
- NIT: tests/test_autopilot.py:1139: the "agent is refused" half of the real-step test calls `agent_env()` directly rather than going through `_claude`. The stubbed test above covers `_claude`, so the two together close the gap. {tests S low}
