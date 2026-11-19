# 179 build report: the feature inventory and the two maps

Everything is built and uncommitted. Requirements R1–R15 are covered. The full gate passes: ruff, 3,178 tests (29 skipped) and `claude plugin validate --strict`. I wrote `plan.md` first and added a "Departures, as built" section to it at the end.

## Slices

1. **`Sdlc-Skill` trailer (R1).** In `scripts/metrics.py`, `summarize()` counts each skill's runs, `trailers()` writes one `Sdlc-Skill: <skill> runs=<n>` line per skill, and `parse_trailers()` reads it back as `skills`. A `Close` commit without the line counts as unrecorded, not as zero. The module docstring adds the line to the contract.
2. **Inventory, use, state and share (R2–R7).** `surface()` in `scripts/retro.py`, returned by `retro()` as `"surface"`.
   - Items are built from the code: `COMMANDS`, `CONFIG_KEYS` and the skill folders. The factory's skills and commands are read as text with `COMMAND_RE`, and only when the factory is enabled or this is the plugin's own repo.
   - Each item's state is `used`, `unused` or `unmeasured` with a reason. Shares leave unmeasured items out, and there is a `_coverage()` block beside them.
3. **Retire candidates (R8).** `RETIRE_AFTER = 3`. A window that couldn't measure an item is skipped: it neither counts toward the three nor breaks the run.
4. **Footprint (R9)** and **growth per release tag (R10)**. Growth is reported only in the plugin's own repo.
5. **`docs/FEATURES.md` (R11, R12, R14).** Eleven sections, one entry per term, and a Mermaid graph of the sections.
6. **`docs/PROCESS.md` (R13).** Three flowcharts: the change, release and retro loops, with a `WAIT:` node for each skill's approval.
7. **Docs (R15).** REFERENCE *Retrospectives*, README pointers to both maps, the scorecard's Simplicity rows marked fed by S5, and AGENTS.md's factory and retro paragraphs.

## Tests added

- **`tests/test_metrics.py::test_close_names_each_skill_it_ran`** (R1): a skill started twice counts twice, the line reads back, and a commit without it is unrecorded.
- **`tests/test_surface.py`** (16 tests):
  - the inventory comes from the code (R2);
  - the command regex matches both scripts' registries, and the factory is listed only when in play (R3);
  - a command call counts once even when `Sdlc-Calls` repeats it, and a key is used only when the config sets it (R4);
  - the three unmeasured reasons, and the factory's `supervised` class (R5);
  - every skill says where it runs (R6);
  - the share leaves out unmeasured items (R7);
  - four retire tests (R8), footprint (R9) and growth (R10);
  - a host's inventory never lists the skills' cases commands.
- **`tests/test_feature_map.py`** (5 tests, marked `portable`): every term the code fixes has an entry (R11); every entry's paths, dependencies and graph nodes are real (R12); the process map holds every skill, stage and WAIT (R13); neither map cites a change number or contains HTML (R14).

I wrote slice 2's code before its tests. To keep the red step honest, I removed the `surface` key from `retro()` and confirmed the new tests failed (13 failed, all with no `surface` to read) before restoring it.

## Departures from the spec (also in `plan.md`)

- **A third skill class, `supervised`**, for `/sdlc-factory:build` and `land`. The factory's supervisor keeps a change's typed command but none of its tool calls (`metrics._supervised()`). Without this class, every command only those skills run would read `unused`. A recorded use still makes any item `used`.
- **`OWN_REPO_COMMANDS`**: `sdlc.py cases` and `run-cases` are left out of a host's inventory. The existing test `test_a_hosts_retrospective_never_mentions_the_cases` failed the first gate run because a host's surface listed `run-cases`.
- **The retire walk reads only `Close` trailers** for earlier windows: one `git show` per window instead of three git calls per change. On this repo that took `surface()` from 35 s to 4.4 s, on a loaded machine. For each kind of item, the walk stops at a window that was measured but had no lines of that kind, meaning it closed before that kind was counted.
- **No changes to `notes.md`.**

## What it shows on this repo

On this repo's history, commands are 61% used. Skills are all unmeasured, because no `Close` commit has an `Sdlc-Skill` line yet. Thirty-three config keys this repo never sets are named as retire candidates. Growth is an empty list, because there are no release tags since the last retrospective.

## Background jobs

An early `sdlc.py retro` run here also started this repo's `retro.test_times`, which runs the whole suite. I couldn't cancel it: there was no TaskStop tool, and `pkill` was refused. It ran until its background time limit stopped it. Nothing depends on it: I checked `surface()` by calling it directly instead.

## Not covered by a test

- Whether GitHub renders the Mermaid blocks has to be checked by eye on the pushed branch.

## Decisions

- DECISION: [default] Read the factory's skill folder names and `factory.py`'s `@command` names as text for the inventory (R3), and record this read in AGENTS.md's factory paragraph. Going ahead with it unless told otherwise.
  - OPTION: read them — `surface` covers the factory too; one more crossing of the factory boundary, its regex pinned by a test
  - OPTION: core only — no policy edit; the inventory misses about a third of the skills and every factory command
  - WHY: the approved spec includes R3, but names the boundary edit as the person's call
- DECISION: [default] Class `/sdlc-factory:build` and `land` as `supervised`: their runs are counted, and commands only they run are `unmeasured`. Going ahead with it unless told otherwise.
  - OPTION: supervised — honest; most `factory.py` commands stay unmeasured until the supervisor's calls are attributed to a change
  - OPTION: inside, as `SKILL_STAGE` implies — simpler; every supervisor-only command reads `unused` and becomes a false retire candidate
  - WHY: R5's rule that an item with no record is never `unused`
- DECISION: [default] Leave the skills' cases commands (`cases`, `run-cases`) out of a host's surface. Going ahead with it unless told otherwise.
  - OPTION: leave them out in a host — keeps the existing rule that a host's retro never mentions the cases
  - OPTION: list them everywhere — a complete inventory; breaks that rule and its test
  - WHY: `test_a_hosts_retrospective_never_mentions_the_cases`

## Evidence

```
$ uv run --group dev pytest -q tests/test_metrics.py::test_close_names_each_skill_it_ran   (before the code)
FAILED tests/test_metrics.py::test_close_names_each_skill_it_ran - KeyError: ...
1 failed in 0.61s
exit: 1

$ uv run --group dev pytest -q tests/test_metrics.py
201 passed in 1.41s
exit: 0

$ uv run --group dev pytest -q tests/test_surface.py   (surface key removed from retro())
13 failed, 2 passed in 49.90s
exit: 1

$ uv run --group dev pytest -q tests/test_feature_map.py   (before the maps existed)
5 failed in 0.14s
exit: 1

$ uv run --group dev pytest -q tests/test_surface.py -k "cases or is_the_code"   (before OWN_REPO_COMMANDS)
2 failed, 14 deselected in 13.00s
exit: 1

$ uv run --group dev pytest -q -n 4 tests/test_feature_map.py tests/test_surface.py tests/test_metrics.py tests/test_modules.py tests/test_nothing_local.py tests/test_windows.py
298 passed in 10.45s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 179   (first run)
FAILED tests/test_retro.py::test_a_hosts_retrospective_never_mentions_the_cases
1 failed, 3176 passed, 29 skipped in 281.74s (0:04:41)
exit: 1

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 179 > /tmp/gate179.log 2>&1; echo "exit: $?"
exit: 0
All checks passed!
3178 passed, 29 skipped in 154.40s (0:02:34)
✔ Validation passed
✔ Validation passed

$ uv run --group dev pytest -q -n 4 tests/test_surface.py tests/test_feature_map.py tests/test_metrics.py::test_close_names_each_skill_it_ran tests/test_retro.py::test_a_hosts_retrospective_never_mentions_the_cases
23 passed in 33.88s
exit: 0
```
