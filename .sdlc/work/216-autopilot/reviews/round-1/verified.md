- KEPT: code: C1: plugins/factory/scripts/factory.py:4292: `_claude()` passes no `env=`, so agent sessions inherit `SDLC_FACTORY_AUTOPILOT_RUN`, and `autopilot_running()` is then true inside them
- KEPT: code: C2: plugins/factory/scripts/autopilot.py (`run_step`), tests/test_autopilot.py: no test runs the real `run_step` subprocess path under the run's env, and none checks that `_claude`'s env lacks the variable
- KEPT: security: C3: plugins/factory/scripts/factory.py:4292: the builder, which has `Bash`, `Edit` and `Write`, inherits the autopilot env through `_claude()` and can use `--by autopilot` itself. Same root cause as C1; the fix is the same
- KEPT: behaviour: C4: plugins/factory/scripts/autopilot.py:289: `sdlc.py status --json` is rejected as `unrecognized arguments: --json`, so `candidates` is always empty and a real run would find no seed

## Notes
- I read `_claude()` (factory.py:4283-4300). Its `subprocess.run` has no `env=`. `autopilot_running()` only checks that the env variable names the held lock. `run_step` adds the variable through `_env()`. That confirms C1 and C3.
- I ran `uv run --script scripts/sdlc.py status --json` in the worktree. It failed with `sdlc.py: error: unrecognized arguments: --json`, which confirms C4. `next_up()` exists in `sdlc.py`, but there is no `--json` output for it.
- For C2 I relied on the claim that `run_step` is stubbed in the tests. I did not read `tests/test_autopilot.py` itself.
- C1 and C3 describe the same defect. One fix in `_claude()` settles both.
