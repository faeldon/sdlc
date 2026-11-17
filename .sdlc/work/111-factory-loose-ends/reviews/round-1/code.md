VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:4232: `_up()` marks any server that exits before answering as a lost port (`True`), so `_serve()` retries it and `shots.json`'s `retries` records it as a lost port. The intent says the retry is for a serve that fails to bind. A dev server that crashes for another reason (a missing dependency, a bad `serve` command) gets three starts and a false "lost" record. Fix: when the process has exited without answering, probe the port with a bind (close it straight after). Only a port that won't bind counts as lost; a port that binds means the server failed on its own, so return `(why, False)` and don't retry. Add a test where `serve` exits without binding (e.g. `exit 1`): one start, no entry in `retries`, and `problem` set.

## Notes

- Nit: `AGENTS.md`'s *Writes before a WAIT* paragraph now has a line of about 150 columns, and `plugins/factory/skills/build/SKILL.md` line 84 is about 170. Rewrap both to the surrounding ~100-column style. The README's *Built on current code* bullet has the same problem.
- Nit: `test_build_names_every_ui_key_start_gives` finds the summary by splitting on a line-broken phrase (`"the base\nbranch's `[ui]` (`ui`:"`). It passes now but breaks if the sentence is re-wrapped. Searching for the `(`ui`:` span on its own would be sturdier.
- Note: the intent's open question (retry on a new port, or have `serve` report its port) is answered by the Approach's retry, so nothing is raised as a DECISION. The retry is also not a full fix for the race: the pre-serve "already answers" check and the serve's own bind still leave a window. That is a limit of the design, not a defect in it.

## What was done well

- `_resolve()` now takes the round's label, and `read_verified()` derives it from the folder name, so a landing round's problem reads `land-1` and a build round's reads `round 1`. Both kinds are pinned by `test_a_landing_verifiers_answer_names_its_landing_round` and the `test_land.py` assertion.
- The spec skill's `fresh` call is the same as the build skill's, placed after `start`'s refusals and before the spec-writer and the WAIT, and it stops on a refusal. `STARTS["spec"]` is `(2, "plan")`, which is also in `STARTS["build"]`, so `fresh` accepts a spec run's change.
- `shots()`'s `finally` still stops the server on every path, and a fresh fixture copy is made for each try, after the previous server has stopped.
- `AGENTS.md` and the README were updated in the same change to name the spec skill's `fresh`, as the contract requires.

## Tests and commands run

- `uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_skills.py tests/test_defaults.py`: 726 passed.
- `uv run --group dev ruff check .`: passed.
- `uv run --group dev ruff format --check .`: 249 files already formatted.
- Not run: the full `./check.sh` gate, and the portable suite on Windows. The new port tests use real sockets and aren't marked `portable`, so I can't say from here how they behave on Windows.
