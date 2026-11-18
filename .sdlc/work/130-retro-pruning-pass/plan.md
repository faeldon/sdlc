---
id: 130
slug: retro-pruning-pass
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 130 — Retro proposes a pruning pass over the test suite · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `CONFIG_KEYS["retro"]["test_times"] = []` with its comment; `"test_times"`
  joins `COMMAND_LISTS`, so `_apply_config()`'s list check and its "must be a list of commands"
  warning cover it with no new code.
- `scripts/indicators.py`: `junit_times(text)` and `drifted_tests(lookback, kind, skip, present)`,
  `DRIFT_LEAST = 3` beside `PAIR_LEAST`, both in the docstring's list. Reuses `_files()` and
  `PAIR_FILES_MAX`, as `co_change()` does. Imports `xml.etree.ElementTree` (stdlib only).
- `scripts/retro.py`:
  - `_evidence(home, commands, timeout=None, limit=None)`: `None` reads `EVIDENCE_TIMEOUT` /
    `EVIDENCE_LIMIT` at call time, so `test_evidence_is_each_commands_output_and_never_a_raise`'s
    monkeypatching still reaches it (a default bound at `def` time wouldn't).
  - `TIMES_TIMEOUT`, `TIMES_LIMIT`, `SLOW_OVER`, `SLOW_LEAST`; two `UNMEASURED` rows.
  - `_skip(home)`: the path filter `_architecture()` defines inline today (change folders and the
    register), lifted so `_tests()` filters the same way.
  - `_lookback(home, trunk) -> (recent, rows, present)`: the walk `_architecture()` does today,
    `rows` as `[(name, numstat rows)]`.
  - `_architecture(..., lookback=None)`: takes the lookback; computes it itself when not given,
    so `test_no_base_branch_means_no_architecture`'s call still holds. Output unchanged.
  - `_times(home, commands)`: runs `test_times` through `_evidence()` with the larger limits,
    reads each row through `junit_times()`, pools the cases and builds the R5 block; rows keep
    `command`, `exit`, `error`, `truncated`, `cases`, never `output` (R6).
  - `_tests(home, cfg, lookback)`: `{"times", "drifted", "due"}`; `drifted` None when `lookback`
    is None (no base branch).
  - `retro()`: builds `_lookback()` once when there's a base branch, passes it to both, adds the
    `tests` key.
- `skills/retro/SKILL.md`: Step 0's `tests` bullet; the process pass's pruning finding (one seed);
  Step 7's line; *Out of scope*. Prose only, no new command or rule.
- `docs/REFERENCE.md`: the `[retro]` sample line, the list of commands `sdlc.py` runs, and a
  *Retrospectives* paragraph (JUnit contract, limits, the `tests` block, the pruning pass).
- Tests: `tests/test_sdlc.py` (R1), `tests/test_indicators.py` (R4, R7), `tests/test_retro.py`
  (R2, R3, R5, R6, R8, R9, R10, R12), `tests/test_skills.py` (R11).
- `tests/test_config_resolution.py`: `test_retro_after_releases_is_a_whole_number` pins the whole
  `[retro]` block, so it gains `test_times: []`. (Found at the gate.)
- `.sdlc/setup.json`: rewritten by `sdlc.py record`. The spec said no `record` was needed, but
  `drift` reports any new config key as `retro.test_times (new): record`, and
  `test_this_repos_setup_record_is_current` fails until it's recorded. The only change is the key
  added to the known list. (Found at the gate.)

- `AGENTS.md`: the *Retrospectives* line names `retro.test_times` among the host commands
  `_evidence()` runs. The spec left this to ship; round 1's review asked for it in the build.

**Departures from the spec, settled in the build.**
- R4's "`seconds` is never 0": a `time` of 0 (or negative, or not finite) reads as None, counted
  `untimed`, since a runner that didn't time a case may write 0.
- R7 with `present` None (the base branch's listing failed): every test file counts as present,
  rather than none. That is the same "unknown" `hotspots()` gives `gone`.
- `slow` keeps exactly the `slowest` rows (R5). The skill works out the multiple of the median
  from `seconds` and `median`, rather than reading a new field.

## Work order

1. **Config key (R1).** Test, then the key and `COMMAND_LISTS`. Stops with a key nothing runs.
2. **`junit_times` (R4).** Pure tests first, then the function. Nothing calls it yet.
3. **Run times through retro (R2, R3, R5, R6).** `_evidence`'s arguments (existing evidence test
   still green), `_times()`, `_tests()` with `drifted` None for now, `tests` in `retro()`. Tests:
   limits, unset/failed/ok, truncated, slow threshold, small block, only retro runs it.
4. **`drifted_tests` (R7).** Pure tests first, then the function.
5. **Drift through retro (R8, R9).** `_skip`, `_lookback`, `_architecture` taking it, `drifted` and
   `due` in `_tests()`, the `UNMEASURED` rows. Tests: host test paths, no base branch, due,
   unmeasured, every key.
6. **Writes nothing (R10).** The two guard tests; they pass on the code from 3 and 5.
7. **The skill and the reference (R11, R12).** Tests first, then the prose.
8. The real fixture from the spec's *Verification*: this repo's own JUnit through `junit_times()`.

## Tests

- R1: `test_test_times_must_be_a_list_of_commands` (`test_sdlc.py`).
- R2: `test_nothing_but_retro_runs_test_times` (`test_retro.py`): `check`, `status`, `config`,
  `readiness` and `retro --report` leave no marker; `retro()` does.
- R3: `test_test_times_get_their_own_limits`: evidence limits shrunk, a slow, long JUnit report
  through `_times()` is read whole. `test_evidence_is_each_commands_output_and_never_a_raise`
  unchanged.
- R4: `test_junit_times_reads_every_testcase`, `test_junit_that_does_not_parse_is_an_error_not_a_raise`
  (`test_indicators.py`, portable).
- R5: `test_times_unset_failed_and_ok`, `test_a_truncated_report_is_a_failure_not_a_partial_read`,
  `test_slow_needs_ten_times_the_median_and_a_second`.
- R6: `test_the_tests_block_stays_small_however_large_the_suite` (5,000 cases, < 8,000 chars).
- R7: `test_a_test_whose_code_moved_without_it_is_drifted`,
  `test_a_test_moved_with_its_code_is_not_drifted`, `test_a_deleted_test_is_never_drifted`,
  `test_a_change_too_large_to_pair_drifts_nothing` (`test_indicators.py`).
- R8: `test_drift_follows_the_hosts_test_paths`, `test_no_base_branch_means_no_drift`.
- R9: `test_due_is_slow_or_drifted`, `test_the_unmeasured_test_signals_are_listed`;
  `test_it_reports_every_key_and_writes_nothing` gains `"tests"`.
- R10: `test_retro_with_test_times_writes_nothing`, `test_retro_commit_refuses_a_changed_test_file`.
- R11: `test_the_retro_proposes_pruning_as_one_seed_and_edits_no_test` (`test_skills.py`).
- R12: `test_reference_names_test_times_and_its_format` (`test_retro.py`).
- Manual (spec *Verification*): `pytest --junitxml` on this repo, `junit_times()` on the file: no
  error, the case count matches pytest's summary.

## Rollback

`git revert` of the change's commit undoes all of it. Nothing is written outside the repo, no data
is migrated, and the new key is optional: a host that set `retro.test_times` gets an
`unknown key retro.test_times` warning after a revert, and removes the line.
