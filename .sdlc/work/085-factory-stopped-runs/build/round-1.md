# Build report: 085, factory stopped runs (round 1)

A stopped factory run now shows up as stopped on the board and in `/sdlc:status`, with its reason and the step that moves it on. The full gate passes (1866 tests) and nothing is committed: `HEAD` is still `90d71b9`.

## Slices built

1. **The stop record, in `factory.py`.**
   - `verdicts <NNN> --head <h> --record` writes `runs/stopped.md` when the next step is `stop`, and removes it on any other step. It writes from the same reading it prints, so the file can't disagree with what `verdicts` said.
   - Without `--head`, `--record` is refused with exit 1. Without `--record`, `verdicts` still writes nothing.
   - The record's text comes from a new function, `stop_text()`, with the new patterns `STOPPED`, `STOPPED_RE`, `NEXT_RE` and `PROBLEM_RE`. Each way on has its sentence in a new `WAYS` table.
   - `loop_state()` now keeps the missing-evidence problems apart from the rest and adds `way` on a stop:
     - `ship` when `HEAD` moved;
     - `mend` when every problem is a missing `## Evidence`;
     - `rerun` otherwise.
   - The loop never reads the record. The module and `cmd_verdicts` docstrings are updated.
   - The build skill's Step 2 now passes `--record`. Step 1 lists the file, and the `stop` step says the supervisor never writes, edits or deletes it.
2. **The board.**
   - A new `_stopped()` reads the record for a factory change at `stage: build` only. A record that won't read becomes a `problems` line.
   - `next_action()` returns the record's sentence, checked after a closed change and before pending decisions.
   - `column()` puts a stopped run under Needs you.
   - `board.html` shows one flag per problem, and the Needs you column's description now says "a decision, a problem or a stopped run".
3. **Status.**
   - `sdlc.py` gets pinned copies of the factory's patterns, named `FACTORY_*`, and `factory_stop()`, which never raises.
   - `rec["stopped"]` is set in status's branch of `main()` at `stage: build` only, so `check` never sees it.
   - The line reads `· stopped, touched <ago>`, with one `⚠` line per problem (cut to 100 characters by a new `_cut()`) and a `→` line under the title.
4. **Docs.**
   - `skills/status/SKILL.md`: a stopped run is neither in flight nor quiet, and rule 3 recommends it with its own `→` step.
   - `plugins/factory/README.md`: the new file in the folder listing.
   - `docs/REFERENCE.md`: the board's Needs you column and the status line.
   - `AGENTS.md`: the two sentences reworded as the spec's Contracts touched 1 and 2 propose.

## Tests added

| Requirement | Test | What it proves |
|---|---|---|
| R1 | `test_record_writes_a_stop_and_removes_it_once_clear` | A stop writes the record and a clear reading removes it |
| R2 | `test_the_record_is_verdicts_own_reading` | The problems are word for word, in order, with the call's way |
| R3 | `test_verdicts_alone_writes_nothing`, `test_record_without_a_head_is_refused` | No write without the flag; no `--record` without `--head` |
| R4 | `test_a_stop_names_its_way` | Each kind of stop gets the right way |
| R4 | `test_a_third_red_gate_names_rerun` | A third red gate is `rerun` (left unmarked: its gate runs `sh`) |
| R4 | `test_a_problem_spanning_lines_is_one_line_of_the_record` | One problem is always one line |
| R5 | `test_a_stale_record_never_stops_the_loop` | A leftover record never stops a clear run |
| R13 | `test_ready_leaves_a_stopped_run_out` | `ready` never lists a stopped run |
| R14 | `test_the_supervisor_records_each_reading` | The skill's `verdicts` call passes `--record` |
| R6 | `test_a_stopped_run_needs_the_person` | Built from 078's round-1 files: Needs you, its flags and its sentence |
| R7 | `test_an_unreadable_stop_record_is_a_problem` | An unreadable record still puts the card under Needs you |
| R8 | `test_a_stop_record_counts_only_at_build` | At design, test or shipped the record is ignored |
| R9 | `test_a_resumed_run_goes_back_to_build` | Removing the record moves the card back to Build |
| R11 | `test_the_factory_parsing_is_a_pinned_copy` (board), `test_sdlcs_copies_of_the_factorys_patterns_match_its_own` (metrics) | Extended to the new patterns |
| R10 | `test_next_up.py::test_a_stopped_factory_run_is_marked_on_its_status_line` | Marked `stopped`, never `quiet`; cut problem lines and the `→` line; `check --strict` output unchanged; ignored at `plan` |

Every new test that touches no shell fake is marked `portable`. The new tests failed first for the reasons expected (missing names, missing `way`, `quiet` on the status line). One exception: the `test_metrics.py` pin was extended after the code existed, so I never saw it fail.

## Changes to `plan.md`

- The Tests section now names the separate third-red-gate test and the one-line test.
- Status's cut width (`STATUS_WIDTH` = 100, `_cut()`) is written down, and an unreadable record in status points to "read runs/stopped.md".

## Notes

- Nothing was left in `notes.md`.
- 078 has since moved on to `stage: test` with an ESCALATE, so it is no longer the live case. The fixture copies its round-1 files as they were, with long lines cut at `…`, under a neutral folder name.

## Evidence

$ ./check.sh
All checks passed!
189 files already formatted
1866 passed in 239.46s (0:03:59)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable
174 passed, 1692 deselected in 39.20s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py tests/test_board.py tests/test_next_up.py tests/test_metrics.py -k "record or stop or way or ready or supervisor or pinned or resumed or copies or touched"
52 passed, 228 deselected in 9.65s
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py verdicts 085 --record
{ "refusals": [ "--record needs --head: without it a stop for HEAD moving would be removed" ] }
exit: 1

$ git rev-parse --short HEAD
90d71b9
exit: 0
