All 12 requirements are built and the gate passes (2,364 passed, 13 skipped). Everything is uncommitted, and `HEAD` is still `6d8905f`. The spec was wrong on one point: it said `.sdlc/setup.json` needed no `sdlc.py record`. `drift` reports any new config key, so I ran `record`, which only adds `retro.test_times` to the known-key list.

**Plan.** `plan.md` replaces the scaffold, written after reading `retro.py`, `indicators.py`, the config loader, the retro skill, `REFERENCE.md` and their tests.

**Slices built, each test-first and seen failing for the expected reason:**
1. **Config key (R1).** `retro.test_times` (default `[]`) joins `COMMAND_LISTS`, so the existing list check covers it. Test: `test_test_times_must_be_a_list_of_commands`.
2. **`indicators.junit_times()` (R4).** Pure. It reads every `<testcase>` at any depth and returns an error for bad input instead of raising. Tests: `test_junit_times_reads_every_testcase` and `test_junit_that_does_not_parse_is_an_error_not_a_raise` (5 bad inputs).
3. **Run times through retro (R2, R3, R5, R6).**
   - `_evidence()` takes `timeout`/`limit`; `None` falls back to `EVIDENCE_TIMEOUT`/`EVIDENCE_LIMIT`, read when it runs, so the existing evidence test's patches still work.
   - `_times()` runs the commands with `TIMES_TIMEOUT`/`TIMES_LIMIT`. A report cut at the limit counts as failed, and no raw output is kept.
   - The new tests check: the two sets of limits stay apart; the unset, failed and ok states; a truncated report fails; the slow threshold at exactly 10× the median and under 1 s; 5,000 cases stay under 8,000 characters; and only retro runs the command.
   - One test was wrong as I first wrote it: 4.0 s against a 0.4 s median is exactly 10×, which the "at least" rule counts as slow. I changed that case to 3.9.
4. **`indicators.drifted_tests()` (R7).** Pure, with `DRIFT_LEAST = 3`. Five tests: drifted, moved with its code, deleted, change too large, and skipped/non-test paths.
5. **Drift in retro (R8, R9).**
   - `_skip()` and `_lookback()` are taken out of `_architecture()`, so `retro()` reads the 30 changes once and passes them to both passes. `_architecture()`'s output is unchanged.
   - `_tests()` returns `times`, `drifted` (`None` with no base branch) and `due`, and `UNMEASURED` gains the two new signals.
   - Tests: host test paths, no base branch, `due`, the unmeasured signals, and the every-key test now includes `"tests"`.
6. **Retro writes nothing (R10).** `test_retro_with_test_times_writes_nothing` and `test_retro_commit_refuses_a_changed_test_file`. Both passed on first run, so I broke the first on purpose (the command appended to a test file) and saw it fail, then restored it.
7. **Skill and reference (R11, R12).**
   - Retro skill: Step 0's `tests` bullet, the pruning finding as one seed, Step 7's line, and *Out of scope*. No new command or permission rule.
   - `REFERENCE.md`: the sample line, the list of commands `sdlc.py` runs, and a *Retrospectives* paragraph.
   - Tests: `test_the_retro_proposes_pruning_as_one_seed_and_edits_no_test` and `test_reference_names_test_times_and_its_format`.
8. **Real fixture.** This repo's own `--junitxml` report read through `junit_times()`: no error, 2,377 cases (2,362 passed + 2 failed + 13 skipped), median 0.207 s. The two failures in that run are the gate failures below.

**Found at the gate, outside the spec's file list:**
- `tests/test_config_resolution.py` pins the whole `[retro]` block, so it gains `test_times: []`.
- `.sdlc/setup.json` was rewritten by `record`, as above.

**What changed in `plan.md`:** it lists those two files, plus three small calls I made where the spec was silent:
- A `time` of 0 (or negative, or not a number) counts as untimed, which is how I read R4's "never 0".
- If listing the base branch's files fails, every test file counts as present, matching how `hotspots()` treats the same failure.
- `slow` holds the same rows as `slowest`; the skill works out the multiple of the median itself.

**Not done:**
- No `checks.md`: every requirement has a test in the suite.
- `notes.md`: nothing.
- At ship, `AGENTS.md`'s *Retrospectives* line still needs `retro.test_times` added, as the spec says.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_sdlc.py -k test_times   (before the key)
1 failed, 237 deselected in 24.12s
exit: 1

$ uv run --group dev pytest -q tests/test_indicators.py -k junit   (before junit_times)
6 failed, 35 deselected in 0.04s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "test_times or times_ or truncated or slow_needs or tests_block"   (before _times)
AttributeError: module 'sdlc_retro' has no attribute '_times' … KeyError: 'tests'
exit: 1

$ uv run --group dev pytest -q tests/test_indicators.py   (before drifted_tests)
5 failed, 41 passed in 0.07s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "drift or due_is or unmeasured_test or every_key"   (before drift was wired)
4 failed, 1 passed, 130 deselected in 19.13s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k test_retro_with_test_times_writes_nothing   (guard broken on purpose: the command appends to a test file)
1 failed, 136 deselected in 2.26s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py tests/test_skills.py -k "reference_names_test_times or pruning_as_one_seed"   (before the prose)
2 failed, 491 deselected in 0.22s
exit: 1

$ uv run --group dev pytest -q -n auto --junitxml=/tmp/sdlc-130-junit.xml   (then junit_times() on the file)
2 failed, 2362 passed, 13 skipped in 99.41s (0:01:39)
error None cases 2377 skipped 13 median 0.207
(the two failures: test_this_repos_setup_record_is_current, "retro.test_times (new): record"; test_retro_after_releases_is_a_whole_number, the pinned [retro] dict)
exit: 1

$ ./check.sh   (first run, after record and the pinned-dict fix)
E501 Line too long (113 > 100) --> tests/test_indicators.py:349:101
Found 1 error.
exit: 1

$ uv run --group dev pytest -q -m portable
393 passed, 13 skipped, 1971 deselected in 188.84s (0:03:08)
exit: 0

$ uv run --group dev pytest -q <every R1–R12 test by node id, plus test_evidence_is_each_commands_output_and_never_a_raise>
29 passed in 36.64s
exit: 0

$ ./check.sh
All checks passed!
249 files already formatted
2364 passed, 13 skipped in 135.31s (0:02:15)
✔ Validation passed
✔ Validation passed
exit: 0

$ git status --short; git log --oneline -1
 M .sdlc/setup.json
 M docs/REFERENCE.md
 M scripts/indicators.py
 M scripts/retro.py
 M scripts/sdlc.py
 M skills/retro/SKILL.md
 M tests/test_config_resolution.py
 M tests/test_indicators.py
 M tests/test_retro.py
 M tests/test_sdlc.py
 M tests/test_skills.py
?? .sdlc/work/130-retro-pruning-pass/
6d8905f Close 114-one-review
