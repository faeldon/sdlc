VERDICT: PASS

I reviewed the whole change, with the closest read on D8, D9, D10 and the settled env findings. They are tested and the tests pass.

- **Settled env findings:** both leaks are closed.
  - `factory.py` takes the markers out of its own environment as it starts (`take_markers()`). Only `loop_env()` puts them back, for a loop's own children.
  - `_claude()` runs with `env=agent_env()`.
  - `test_an_agent_session_never_carries_the_loops_markers` stubs `subprocess.run` and checks the session's env lacks both markers and keeps the rest.
  - `test_the_changes_own_code_never_runs_as_a_loops_child` runs the real `gate` and `accept` through `run_step`, with the host check and the acceptance check each writing `env` to a file. It asserts neither file holds `AUTOPILOT_RUN_ENV` or `TRAIN_RUN_ENV`.
- **Real subprocess path:** `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs a real `run_step`. `answer --by autopilot` is refused with the lock free, refused under `agent_env()` while the lock is held, and accepted under the loop's env.
- **`status --json`:** `test_candidates_come_from_the_real_status_json` calls the real `sdlc.py`, not a stand-in. It checks the ids, the `issues` values ([], [], [7]), and that a seed with an issue is a candidate only when named.
- **D8:** `test_default_guards_hold_the_sensitive_paths` checks the exact guard list. It takes the policy and review docs, `irreversible` and `sensitive` from the base branch, and the change's own `[review]` adds nothing. It would fail if `_default_guards()` dropped `sensitive`.
- **D9:**
  - `test_a_seed_with_an_issue_is_a_candidate_only_when_named` covers `[12]`, `None` and `[]`, both unnamed and named.
  - `test_a_seed_with_an_issue_is_opened_with_closes` checks the `closes: [12, 15]` frontmatter line and that `intent_closes()` reads it back.
  - The same test checks that a seed whose `Issue:` line can't be read is held, and that no intent agent ran for it.
- **D10:** a documentation change, so it needs no test.

## Notes
- Gate record `build/round-4.gate.md`: `./check.sh` passed (the builder reports 3947 passed, 29 skipped).
- I ran `uv run --group dev pytest -q tests/test_autopilot.py -n 0` in the foreground: 54 passed.
- `checks.md` has an acceptance check, "It reads its env", but it sits inside a test fixture string, not in the change's own `checks.md`. I did not run it.
- Every R1–R28 in `plan.md`'s Tests list maps to a named test, and I found no test that can't fail.
- NIT: tests/test_autopilot.py:1218: the test that uses the real `status --json` is marked `@needs_uv`, so it is skipped where `uv` is absent. The D9 and `issues` coverage there then rests on the stubbed `candidates` test alone {tests S low}
