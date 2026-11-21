VERDICT: PASS

The one change kept from last round is done. It said the builder's own code, run by `gate`, `accept` or a train's tip gate, still inherited `AUTOPILOT_RUN_ENV`.

- **Fix:** `take_markers()` is now `main()`'s first step (`factory.py:6652`). It moves `AUTOPILOT_RUN_ENV` and `landing.TRAIN_RUN_ENV` out of `os.environ` into `LOOP_MARKERS`.
- **Gate, accept and tip gate:** `_run_check()`, `_sdlc()` (so `sdlc.py accept`), `_run_env()` and git hooks no longer see either marker. `_run_env()` builds on `loop_env()`, which gives the markers back only to a loop's own children.
- **Pass-through:** `autopilot.py:393` builds each loop child's env from `loop_env()` and adds the lock. So `--by autopilot` still works for those children, and for nothing the change's code runs.
- **Gate result:** `build/round-3.gate.md` reads `GATE: PASS`. I did not run the gate or any tests myself.

## Notes
- The tests I read cover the agent-session env and a real `run_step` that passes `--by autopilot` under the lock and is refused with an agent's env. The round-2 section of `tests/test_autopilot.py` has a `CHECKS` fixture that writes the env a `checks.md` command ran with. I read these three and did not run them.
- `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` and the real-`status --json` test close last round's "test is stubbed" gap. The `CHECKS` fixture is the one that covers the acceptance path.
- Doing the removal once at process start, rather than per call site, is a sound design. Anything the factory later starts is safe by default.
