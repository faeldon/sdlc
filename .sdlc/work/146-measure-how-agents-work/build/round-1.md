All 16 requirements are built and the full gate passes (`./check.sh`: 2623 passed, 18 skipped). Nothing is committed: the work is uncommitted in the worktree and HEAD is still `25c2427`.

## Plan
I wrote `plan.md` (five slices) after reading the code, and added an "As built" section for two departures from it:
- **`models` is passed by position, not keyword.** `measure_change()` calls `read_events(..., roles, models)` that way. Passing it as `models=` broke `test_a_reader_that_fails_never_stops_the_close`: that test's stand-in takes only `*_`, so close recorded `TypeError` instead of `RuntimeError`.
- **One existing retro test changed.** `test_retro_prints_each_change_s_numbers_only_when_asked` now also removes `spend.agents.changes` from the `--metrics` output before comparing. R15 makes that list a second thing only `--metrics` prints.

## Slices built
1. **Recognising shell commands** (`scripts/metrics.py`). The word splitter was pulled out of `_prompt_name()` into `_segments()`; its output is unchanged and the existing tests still pass. A new pure `_shell(command, check)` returns whether a command wrote a file, went to the background, or ran tests. It also adds `_program()`, `TEST_RUNNERS` and `BROKE_RE`.
2. **Counting in the loop `_run()` already makes.** `_behaviour()` is called once per entry inside that loop, under a `try`. The `subagent` event gains `behaviour`, `calls` and `model`. `summarize()` adds them up by role, or drops them and adds ` behaviour=failed` to coverage. `trailers()` adds `model=` and the six counts at the end of `Sdlc-Role`, plus a new `Sdlc-Calls` line. `parse_trailers()` reads `Sdlc-Calls` into `calls`.
3. **Model per session** (`scripts/sdlc.py`). A new `_agent_models()` reads `runs/costs.jsonl` from the branch and skips lines that don't parse.
4. **Retro** (`scripts/retro.py`). `_agents()` groups role lines by `(role, model)` and is returned as `spend.agents`. `_agents_text()` adds the "Agents by role and model" table to `{{spend}}`. Without `--metrics`, `cmd_retro()` leaves out `spend.agents.changes`.
5. **Docs.** The `metrics.py` docstring now describes the contract (the six counts, `model=`, `Sdlc-Calls`, the extended `subagent` event, the `models=` argument, and the unrecorded rule). `docs/REFERENCE.md` *Metrics* has a new paragraph saying the same for a host.

## Tests added and what they prove
- **R1, R2:** `test_a_role_s_behaviours_are_counted_from_its_transcript`. One of each behaviour, each counted exactly 1; an interrupted call adds nothing.
- **R3:** `test_a_shell_edit_is_known_by_its_command`, 20 cases. Every named shape counts; `2>&1`, `> /dev/null`, a temp dir, `grep '>'`, `sed -n`, a read-only `python -c` and a heredoc body don't.
- **R4:** `test_a_backgrounded_command_is_known_by_its_result` covers `run_in_background`, the harness timeout (`timedOutAfterMs`) and a trailing `&`, but not `a && b`. `test_a_command_ending_in_a_lone_ampersand_goes_to_the_background` covers the `&` half on its own.
- **R5:** `test_a_test_run_is_known_by_its_program`. Runners are found past `uv run`, `npx`, `python -m` and `VAR=`, as are the host's check and the hand gate; `grep pytest x` and `cat pytest.ini` aren't.
- **R6:** `test_a_broken_build_is_a_failed_parse_after_an_edit` (4 cases) and `test_a_broken_build_is_read_from_text_blocks_too`. Only a parse or import failure right after an edit counts.
- **R7:** `test_a_role_s_tools_are_listed_by_name`. Finds `Sdlc-Calls: builder Bash:sed=2 Edit=1`, and checks no name's count across roles exceeds its `Sdlc-Tool` count.
- **R8:** `test_a_role_s_model_comes_from_its_costs`. Covers one model, two models sorted, a name with `:` and `/` turned into a plain word, and no model.
- **R9:** `test_measuring_reads_each_transcript_once`, in `tests/test_archive.py` because it needs that file's factory-change repo. `measure_change()` reads each transcript once, takes `model=model-a` from `costs.jsonl`, and writes `Sdlc-Calls`.
- **R10:** `test_a_behaviour_count_that_fails_drops_only_its_fields`. Forces `_behaviour` to fail; the `Sdlc-Totals`, `Sdlc-Stage` and `Sdlc-Tool` lines come out identical.
- **R11:** `test_behaviour_trailers_carry_no_text`. No marker string, `/`, `~` or space inside a value on the role lines.
- **R12:** `test_a_close_from_before_behaviours_parses_as_before`. Pins an old commit body's parsed dict.
- **R13–R15:** `test_retro_compares_agents_by_model`, `test_retro_leaves_agents_from_before_behaviours_out` and `test_retro_prints_a_change_s_agent_counts_only_with_metrics`.

## Notes
- No `notes.md` was written; nothing was left over.
- During the build, one serial run of `pytest tests/test_archive.py tests/test_train.py` (no `-n auto`) hit the 120s limit and was moved to the background; it finished with exit 0. After that, every run used `-n auto` or a long foreground timeout. It is the same pattern `bg=` now counts.

No decisions raised. No UNTESTABLE requirements: R16 is the review's to check, as the spec says.

## Evidence

$ ./check.sh > /tmp/gate146.log 2>&1; echo "exit: $?"; tail -4 /tmp/gate146.log
✔ Validation passed
exit: 0

$ grep -E "passed|failed" /tmp/gate146.log | tail -3
2623 passed, 18 skipped in 109.51s (0:01:49)
✔ Validation passed
✔ Validation passed

$ uv run --group dev pytest -q -m portable -n auto
461 passed, 18 skipped in 23.33s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_archive.py
148 passed in 15.57s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_metrics.py
311 passed in 11.62s
exit: 0

$ ./check.sh (first run, before passing `models` by position)
FAILED tests/test_archive.py::test_a_reader_that_fails_never_stops_the_close
1 failed, 2622 passed, 18 skipped in 146.29s (0:02:26)
exit: 1

$ uv run --group dev ruff check scripts tests --output-format concise
All checks passed!
exit: 0

$ git log --oneline -1
25c2427 Close 139-landing-train
