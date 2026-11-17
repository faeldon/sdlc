I fixed all four gaps in 111 and left everything uncommitted on its branch. The full gate (`./check.sh`) passes: 2194 tests passed, 9 skipped. I also wrote a `plan.md`, since the Approach touches more than a couple of files.

## Slices built

1. **Landing rounds named `land-<n>` (2026-11-17-80).** `_resolve()` now takes the round's name instead of its number. `read_verified()` picks the name from the folder of the file it reads: `land-<n>` for `reviews/land-<n>/`, `round <n>` for any other. So a landing round's problem now says "C9, which no change of land-1 is".
2. **A lost port gets a new one (2026-11-17-19).** Starting the dev server has moved out of `shots()` into a new `_serve()`, which tries up to 3 ports (`SERVE_TRIES`). It moves to a new port when another process got there first, which shows up three ways:
   - something already answers on the port before the server starts;
   - the server exits before answering;
   - the port answers but the server it started has already exited, so it is someone else's server.

   Each lost try goes into `shots.json` under `retries`, with its port and why. A server that times out or can't start at all isn't retried. The fixture is copied fresh for each try, since a server may have written into the last copy. If all three tries fail, the problem reads "the dev server came up on none of 3 ports: …".
3. **The spec skill runs `fresh` (2026-11-17-64).** Step 0 now explains `base` and `behind` and then makes the same `factory.py fresh <NNN>` call as the build skill, under the same exception that lets it write before the approval question. If `fresh` refuses, the skill shows why and stops. `allowed-tools` has the new `fresh` rule. Step 1 shows `behind` and what `fresh` did (its state, `from` → `head`, and the `undo`) next to the draft.
4. **The build skill names `fixture` (2026-11-17-67).** Its summary of `start`'s `ui` now lists `fixture` with `serve`, `shoot` and `paths`.

I also updated two docs to match: the factory README (lost ports get a retry; the spec skill runs `fresh`) and AGENTS.md (*Writes before a WAIT* and *The factory* now mention `fresh` from the spec skill as well).

## Tests added

I watched each one fail for the expected reason before writing the fix:
- **`test_a_landing_verifiers_answer_names_its_landing_round`** (test_factory): a landing round's problems say `land-1`, a build round's say `round 1`.
- **`test_a_landing_mend_is_once_a_role_a_round`** (test_land, extended): `land-verdicts` reports "C9, which no change of land-1 is" and never "round 1". It failed with the old line put back in and passed with the fix.
- **`test_shots_take_a_new_port_when_theirs_is_lost`** (test_factory): with the first port already answering and the second only bound, it shoots on the third port and records two retries. With every try lost, there's a problem and no server is started. Before the fix, it took screenshots of the other process's port.
- **`test_factory_spec_brings_the_change_up_to_date_before_its_spec_writer`** and **`test_build_names_every_ui_key_start_gives`** (test_skills): these check the skill text. They're in `test_skills.py`, where every other skill-text test lives, not in the files the intent named.

## plan.md and notes.md
- `plan.md` is written and was updated during the build to add the README and AGENTS.md edits and the `test_skills.py` home for the skill tests.
- Nothing was left for `notes.md`.

- DECISION: [default] Should the UI review's server retry on a new port, or have `[ui] serve` report the port it bound (`{port}` = 0)? Options: retry; report. Going ahead with retry, as the Approach says: it needs nothing from a host's serve command and adds no placeholder.
- DECISION: [default] Should the spec skill show `behind` and what `fresh` did next to the draft, or inside the approval question? Options: next to the draft; in the question. Going ahead with next to the draft, as the build skill does. The question's literal text stays the same, and once `fresh` has run, `behind` in the question would always be 0.

## Evidence

```
$ ./check.sh
All checks passed!
245 files already formatted
2194 passed, 9 skipped in 138.09s (0:02:18)
✔ Validation passed
exit: 0
```

```
$ uv run --group dev pytest -q tests/test_factory.py::test_a_landing_verifiers_answer_names_its_landing_round
FAILED tests/test_factory.py::test_a_landing_verifiers_answer_names_its_landing_round
E   assert 'C9, which no change of land-1 is' in 'reviews/round-1/verified.md answers code: C9, which no change of round 1 is'
exit: 1
```

```
$ uv run --group dev pytest -q tests/test_land.py::test_a_landing_mend_is_once_a_role_a_round   # with the old label line put back
1 failed in 2.00s
exit: 1
```

```
$ uv run --group dev pytest -q tests/test_factory.py::test_shots_take_a_new_port_when_theirs_is_lost
E   KeyError: 'retries'
exit: 1
```

```
$ uv run --group dev pytest -q tests/test_skills.py -k "factory_spec_brings or every_ui_key"
E       AssertionError: fresh runs in Step 0's bash
E           AssertionError: fixture
2 failed, 350 deselected in 0.14s
exit: 1
```

```
$ uv run --group dev pytest -q tests/test_factory.py::test_a_landing_verifiers_answer_names_its_landing_round tests/test_factory.py::test_shots_take_a_new_port_when_theirs_is_lost tests/test_land.py::test_a_landing_mend_is_once_a_role_a_round tests/test_skills.py::test_factory_spec_brings_the_change_up_to_date_before_its_spec_writer tests/test_skills.py::test_build_names_every_ui_key_start_gives
5 passed in 16.60s
exit: 0
```
