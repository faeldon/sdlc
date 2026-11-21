# Build report — 216-autopilot, round 2 (rework of round 1)

I've fixed all four kept findings and the nit, and the full gate is green: 3934 passed, 29 skipped. Nothing is committed; `HEAD` is still `9b4eadd`.

## The kept changes

- **code (contract): `_claude` passed its whole env to agent sessions.** `_claude()` now runs every session with `env=agent_env()`. That is the environment without `AUTOPILOT_RUN_ENV` or `landing.TRAIN_RUN_ENV`, so nothing an agent runs counts as one of a loop's children. The prompt's autopilot part and the gate on `cmd_autopilot_agent` are still decided before `_claude` runs. The new test `test_an_agent_session_never_carries_the_loops_markers` checks the session's env under a held lock.
- **code (correctness): no test ran the real `run_step` path.** The new test `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs a real `run_step` child: `answer --by autopilot`.
  - With the lock free, it is refused.
  - With the lock held and the loop's env, it is accepted, and the ledger line reads `decided_by: autopilot`.
  - The same command run with `agent_env()` is refused.
- **security: the builder could pass `--by autopilot`.** This is the same bug as the first finding, fixed by the same change and covered by both new tests. I checked that the tests catch it: with `agent_env()` put back to the whole environment, both fail; restored, both pass.
- **behaviour: `sdlc.py status --json` didn't exist.** I added `status --json`. It is read-only and prints `next_up()`'s items (id, group, rule, label, kind, theme) and its warnings. The new test `test_candidates_come_from_the_real_status_json` runs the real `sdlc.py` with nothing stubbed: a high-severity bug is a candidate and a plain idea is not.
  - On a scratch repo, `status --json` prints a plain idea in the `decide` group.
  - A first gate run failed three tests that build the status arguments by hand without `json`. `cli_status` now reads the flag with `getattr`.
- **Nit: `land.batch` was re-read on every pass.** `--begin` now fixes it in the state as `config.land_batch`, and `starts()` reads it from there. `test_autopilot_begin_writes_the_state_once` checks it.

## Tests

- Added: the three tests above. Extended: `test_autopilot_begin_writes_the_state_once`.
- `tests/test_autopilot.py` now has 50 tests.
- A targeted run of `tests/test_autopilot.py`, `tests/test_factory_agent.py` and `tests/test_sdlc.py`: 446 passed.
- `tests/test_setup_lifecycle.py` and `tests/test_update.py` after the `getattr` fix: 88 passed.

## plan.md and notes.md

plan.md now names `agent_env()` and `status --json`. notes.md has a *Round 1* section, and its open item about the end-to-end test now says one test runs a real child but none runs the whole loop with a fake `claude`.

No new decisions this round. Round 1's six `[default]` decisions still stand.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_autopilot.py -k "markers or real_step"   (agent_env() temporarily returning the whole os.environ)
FAILED tests/test_autopilot.py::test_an_agent_session_never_carries_the_loops_markers
FAILED tests/test_autopilot.py::test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does
2 failed, 47 deselected in 0.91s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py -k "markers or real_step"
2 passed, 47 deselected in 1.07s
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py -k "real_status"
1 passed, 49 deselected in 0.59s
exit: 0

$ uv run --quiet --script <path-to-clone>/.claude/worktrees/216-autopilot/scripts/sdlc.py status --json   (in a scratch repo with one idea)
{"next_up": {"items": [{"rule": "idea", "label": "idea", "title": "Keep drafts", "id": "2026-11-21-1", "kind": "idea", "theme": null, "age_days": 0, "command": "/sdlc:intent 2026-11-21-1", "group": "decide"}], "warnings": []}}
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_autopilot.py tests/test_factory_agent.py tests/test_sdlc.py
446 passed in 17.49s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_setup_lifecycle.py tests/test_update.py
88 passed in 4.48s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 216   (before the getattr fix)
FAILED tests/test_setup_lifecycle.py::test_a_release_that_changed_nothing_leaves_no_nudge
FAILED tests/test_setup_lifecycle.py::test_a_doc_drift_cannot_read_keeps_the_nudge
FAILED tests/test_update.py::test_status_reads_the_cache_alone - AttributeErr...
3 failed, 3931 passed, 29 skipped in 424.74s (0:07:04)
exit: 1

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 216
All checks passed!
352 files already formatted
3934 passed, 29 skipped in 341.54s (0:05:41)
✔ Validation passed
exit: 0

$ git log --oneline -1
9b4eadd Close 215-evidence-exits
exit: 0
