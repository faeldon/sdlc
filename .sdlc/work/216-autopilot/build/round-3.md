# Build report — 216-autopilot, round 3 (rework of round 2)

I've fixed C1, and the full gate is green: 3935 passed, 29 skipped. Nothing is committed; `HEAD` is still `9b4eadd`.

## The kept change

- **security C1: the host's check, `accept` and the train's tip gate inherited `AUTOPILOT_RUN_ENV`.** I fixed it at the source rather than adding `env=` to each spawn.
  - `factory.py`'s `main()` now first moves both loop markers out of its own `os.environ` into `LOOP_MARKERS` (`take_markers()`). So no process it starts inherits them: not the host's check, not `sdlc.py` (or the acceptance checks it runs), not git and its hooks, not the dev server or `claude`.
  - Only `loop_env()` gives the markers back. `autopilot.run_step()` and the train's `_run_env()` are its only callers, so only a loop's own `factory.py` children get one.
  - A train autopilot started still passes its marker on to its `land --by autopilot` children.
  - `autopilot_running()` and `cmd_train()` read the markers through `loop_marker()`.
  - A per-call fix would have meant about twenty spawn sites, many in sensitive landing code, and any one missed would reopen the hole.
- **The arbiter's note that `sdlc.py status` still has no `--json`** is out of date: round 2 added it (`scripts/sdlc.py:10835`), and `test_candidates_come_from_the_real_status_json` runs it unstubbed.

## Tests

- **Added `test_the_changes_own_code_never_runs_as_a_loops_child`**, which runs a real `run_step` of `gate` and `accept` while the lock is held. The base branch's check and a `checks.md` check each write their env outside the tree, and neither may hold either marker.
  - It was red first, for the reason the reviewer gave: the gate's env held `SDLC_FACTORY_AUTOPILOT_RUN`.
  - It is green after the fix, together with round 2's two env tests.
- **Changed `tests/test_modules.py`**: the landing pair now counts autopilot.py as a sibling (it calls `loop_env()`), as autopilot.py's own pair already does.
- **Runs:** the three env tests: 3 passed. `tests/test_modules.py`: 40 passed. The full gate: 3935 passed.

## plan.md and notes.md

AGENTS.md's factory paragraph now names `take_markers()` and `loop_env()`. notes.md has a *Round 2* section saying what `agent_env()` missed and what replaced it. plan.md is unchanged this round.

No new decisions this round.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_autopilot.py -k "own_code"   (before the fix)
E           assert 'SDLC_FACTORY_AUTOPILOT_RUN' not in 'STARSHIP_SH...=truecolor\n'
E               SDLC_FACTORY_AUTOPILOT_RUN=<tmp>/pytest-of-<user>/pytest-5397/test_the_changes_own_code_neve0/repo/repo/.git/sdlc-factory-autopilot-run.lock
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py -k "own_code or real_step or markers"
3 passed, 48 deselected in 1.25s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 216   (before the test_modules sibling fix)
FAILED tests/test_modules.py::test_the_line_between_script_and_module_holds[landing]
1 failed, 3934 passed, 29 skipped in 232.90s (0:03:52)
exit: 1

$ uv run --group dev pytest -q tests/test_modules.py
40 passed in 25.61s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 216
All checks passed!
359 files already formatted
3935 passed, 29 skipped in 290.31s (0:04:50)
✔ Validation passed
exit: 0

$ git log --oneline -1
9b4eadd Close 215-evidence-exits
exit: 0
