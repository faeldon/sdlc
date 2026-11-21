VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:3499: **The builder can still use `--by autopilot` through the gate and `accept`.** `_run_check()` runs the base branch's `[commands] check` without an `env=`. So when the loop runs `gate NNN` through `run_step()`, which sets `AUTOPILOT_RUN_ENV` (autopilot.py:390–400), the host's check inherits the variable while the loop holds the lock. That check runs the change's own code: its tests, a `conftest.py`, anything they import. The `accept` step works the same way. `_sdlc()` removes only `UNSET_FOR_SDLC` (`SDLC_CLOSE_RAN`, `SDLC_OWN_SCRIPT`, `VIRTUAL_ENV`), so `sdlc.py accept` runs the `checks.md` commands, the builder's tests included, with the variable set. A train's tip gate (`gate --land`, and `--build`) inherits it too, through `_run_env()`, which builds on `os.environ`. **Exploit:** a builder misled by a seed's text doesn't need its own `Bash` anymore. It writes a test module that runs `factory.py answer NNN Dk --by autopilot` when it is imported (or `stage NNN test`, then `train --begin … --by autopilot` and `train --run`). The next `gate` step then runs that code as one of the loop's children, and `autopilot_running()` is true for it. This is the same breach last round's kept finding named. `agent_env()` closed only the direct agent-session path, and the change's own code still runs under the variable. **Fix:** remove `AUTOPILOT_RUN_ENV` and `landing.TRAIN_RUN_ENV` (use `agent_env()`) wherever the factory runs a host's command or code the change wrote:
  - pass `env=agent_env()` in both branches of `_run_check()`, and in the `[ui]` server and screenshot runs that go through `_sh()`;
  - add both markers to the env `_sdlc()` builds for `accept`. `sdlc.py` never reads either marker, so this costs nothing.

  Add a test: under a held lock with the loop's env, stub `subprocess.run` for `gate` and for `_sdlc(["accept", …])`, and assert that neither env contains `AUTOPILOT_RUN_ENV`. Better, run a real `gate` whose `check` is `env | grep SDLC_FACTORY_AUTOPILOT_RUN && exit 1 || exit 0`.

## Notes

Last round's kept changes:
- **Done: agent sessions no longer inherit the loop's variables.** `_claude()` now passes `env=agent_env()` (factory.py:4285–4303), which removes `AUTOPILOT_RUN_ENV` and `landing.TRAIN_RUN_ENV`. `test_an_agent_session_never_carries_the_loops_markers` covers it. The builder's report shows both new tests fail when `agent_env()` is put back to the whole environment, so the tests really check the fix. The CHANGE above is the remainder of the same trust boundary, reached a different way. It is not a re-raise of the agent-session line.
- **Done: one test now runs a real child.** `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs a real `run_step` with the lock free, with the lock held, and with the session's env.
- **Done: `status --json` now exists.** It is read-only and prints only `next_up` items and warnings, with no paths or secrets. `getattr(args, "json", False)` keeps the callers that build the status arguments by hand working.
- **Done: the `land.batch` nit.** `--begin` fixes it in the state as `config.land_batch`, and `starts()` reads it from there.

Medium:
- **Seed text reaches the agents' prompts.** The seed's title and body (possibly from a public issue) go into the intent-writer's and spec-writer's prompts. The script, not the prompt, is the boundary for `--by autopilot` and for `hold_causes()`, so I rate this Medium, not High. It stays acceptable only once the CHANGE above closes the last route to the marker.

Gate: `build/round-2.gate.md` is green (PASS, `./check.sh`, 237 s). The builder's report records 3934 passed and 29 skipped.

What I checked: the round-2 report, `autopilot_running()` and `by_refusal()`, `agent_env()` and `_claude()`, `run_step()` and `_env()`, the steps the loop runs (`gate`, `accept`, `land-check`, `train`), how `_run_check()`, `_sdlc()` and `landing._run_env()` build their envs, and the `status --json` diff. I ran only read-only greps and `sed`. I ran no tests.
