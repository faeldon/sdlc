VERDICT: PASS

The finding kept from last round is fixed. I found no new Critical or High finding in the reworked paths.

- DECISION: [default] Treat `AUTOPILOT_RUN_ENV` as protection against *inheriting* the marker by accident. It is not a boundary against a process that sets the marker on purpose, and the docs should say so. `autopilot_running()` (factory.py:3465) checks two things: the env names `<git-common-dir>/sdlc-factory-autopilot-run.lock`, and some process holds that lock. That path is public and predictable. So while the loop runs, any process running as the same user can set the variable itself and pass `--by autopilot`. That includes a builder session started as a loop step, whose `Bash` runs with `--permission-mode auto`. For example, seed text could tell it to run `SDLC_FACTORY_AUTOPILOT_RUN=$(git rev-parse --git-common-dir)/sdlc-factory-autopilot-run.lock factory.py answer NNN Dk --by autopilot`. Spec R2 defines the check exactly this way, and earlier rounds passed that design. I'm raising it as a decision, not a CHANGE. A secret token would not close it either: a same-user process can read any file the loop can.
  - OPTION: accept and document — say in AGENTS.md and the factory README that `--by autopilot` stops accidental inheritance, not a same-user process that sets the marker deliberately. The real limit on a misled builder is its permissions and sandbox. Costs nothing, but leaves the risk open.
  - OPTION: sandbox the builder's `Bash` during autopilot (Claude Code's sandbox, or a deny rule on `factory.py` and on setting `SDLC_FACTORY_*`) — actually closes it, but deny rules are best-effort and could block legitimate builder commands.
  - OPTION: make the loop's own steps check the ledger themselves — for example, before `land` the loop checks that each `→ decided by autopilot:` line matches a call recorded in `AUTOPILOT_STATE`, and stops if not. A forged call is then caught before it lands. It costs code in `autopilot.py`, and the state file can be forged the same way.
  - WHY: no in-process check can tell a deliberate same-user process from the loop's child. Writing the limit down keeps the docs from claiming a boundary the code doesn't have.

## Notes

**The kept change is done.** `main()` now calls `take_markers()` first (factory.py:3447, 6652). It moves `AUTOPILOT_RUN_ENV` and `TRAIN_RUN_ENV` from `os.environ` into `LOOP_MARKERS`. Only `loop_env()` puts them back, and only `autopilot._env()`/`run_step()` and `landing._run_env()`/`_run_one()` call it, both for `factory.py` children. Each child pops the markers again as it starts. So none of these see either marker:
- `_run_check()`'s host check, including the train tip's `gate --land`/`--build`
- `_sdlc()` (factory.py:5357, built on the cleaned `os.environ`), and so `sdlc.py accept` and the `checks.md` commands
- the git calls in landing.py:1642 and 2882
- `_claude()`, which also passes `env=agent_env()` explicitly

`autopilot_running()` and landing.py:1978 read the marker through `loop_marker()`, so the processes that are meant to see it still do.

**What I checked and ran:**
- I traced every `env=` and every `os.environ` use in `factory.py`, `landing.py` and `autopilot.py`.
- I ran `test_an_agent_session_never_carries_the_loops_markers` and `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does`: both pass.
- `build/round-3.gate.md` shows the gate passed (`./check.sh`, exit 0).

**Medium (test gap):** no test pins `take_markers()` for a host command. If a later edit dropped the pop, or moved it after a subprocess starts, the gate's host check would quietly inherit the marker again. Suggested test: run a real `factory.py gate` (or `check`) under `run_step`, with `[commands] check` set to a script that prints its env, and assert the output lacks both markers.

- NIT: tests/test_autopilot.py:1140: no test that a host's `[commands] check`, run by a `gate` step under the loop, lacks `AUTOPILOT_RUN_ENV`/`TRAIN_RUN_ENV`; `take_markers()` is untested {tests S med}

**Done well:** the fix sits at one point that covers every case. Stripping the markers when the process starts covers every subprocess it later starts, so nobody has to remember an `env=` at each call site.
