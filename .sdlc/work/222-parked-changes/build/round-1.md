I built all 18 requirements, test first. The final full run passed (3980 passed, 29 skipped, plugin validation passed), lint and format are clean, and everything is left uncommitted with `HEAD` unchanged at `3bafdfd`.

## Slices built (in `plan.md`'s order)

1. **Config and the busy answer (R1, R3, R4).** `[park]` is read from the base branch only, with no default exit code. A checkout's own copy is warned about and ignored. `busy_of()` reads the three `SDLC-BUSY-*` lines. `park_fields()` works out since, retry and deadline. `park_text()` and `read_park()` write and read the record.
2. **The gate parks (R2, R4, R5, R12).** A busy exit, or a wait for a gate slot past `SLOT_WAIT` (one hour), writes a vouched `runs/parked.md` and no gate attempt. `gate` then prints `verdict: BUSY` and exits 1. Any attempt that isn't busy removes the park.
3. **`verdicts` reads it (R6–R9).** `loop_state()` and `cmd_verdicts()` take `now`. A park is `parked` before its retry, `gate` from the retry, and a stop with way `parked` at the deadline. An unvouched or unreadable record is a stop to rerun. The deadline is capped by the base branch's setting. `--record` removes a stale park and writes `STOPPED: parked`. The new way is in both copies of `STOPPED_RE` and in `FACTORY_STOP_NEEDS`.
4. **Landing and `check` (R12–R14).** A busy landing gate writes nothing and returns a `problem`, so the train stops; `landing.py` is untouched. `check` passes the busy exit code through with a `busy:` line on stderr. Past `SLOT_WAIT`, `check` exits 1.
5. **`park --wait` / `--clear` and `start` (R10, R11).** `start --for build` reports the park and whether it has expired. The build skill gets one `park *` rule, which covers both commands, plus the `parked` step, the `parked` stop, and `--clear` on a rerun's yes.
6. **Autopilot (R15).** A `parked` reading runs no command, and the change keeps `retry` and `deadline`. `starts()` skips it until the retry. `run_loop()` waits in slices of at most 30 s and doesn't end while a change is parked.
7. **Status and the board (R16).** `factory_records.read_park()` and `park()` are pinned copies of the factory's reader. The card shows the park at the gate position. `needs_of()` adds `parked past its deadline: free <resource>`.
8. **The table and docs (R17, R18).** `STEPS` is the list of every step `verdicts` can name. The factory README gains *The loop's states* table and `[park]` in its configuration, `REFERENCE.md` gains the host's side, `FEATURES.md` gains a `parked` entry, and the `AGENTS.md` sentence is changed as the spec worded it.

## Tests added
- **`tests/test_factory_park.py` (new, 21 tests):** R1–R8, R9's read-back through `read_stop()`, R10, R11's `start`, R12, R14 and R17. Each test is listed by requirement in `plan.md`.
- **`test_land.py`:** `test_a_busy_landing_gate_is_a_problem_never_an_eject` (R13).
- **`test_autopilot.py`:** `test_autopilot_waits_out_a_park_and_holds_past_its_deadline` (R15).
- **`test_sdlc.py`:** `test_a_park_past_its_deadline_needs_the_person` (R16).
- **`test_board.py`:** the card test and the status test (R16).
- **`test_modules.py`:** the two `read_park` pins, plus the new names in `RECORD_NAMES` and `RECORD_FILES`.
- **`test_feature_map.py`:** `parked` added to `VOCABULARY`.
- **Existing tests extended for the new key and way:** `test_config_defaults_and_its_warnings`, `test_each_way_on_fits_two_lines_at_phone_width`, `test_the_stop_record_says_why_and_reads_as_before` and `test_status_records_only_gain_keys`.

**Red first, with exceptions.** Slices 1–3, 5, 7 and 8 failed before their code. The slot-wait and `check` tests were written after the code; the `check` test fails when the change is broken on purpose. The slot test wasn't run that way, because without the bound it hangs rather than fails. The autopilot test's red run against `HEAD`'s `autopilot.py` failed only because `_pause` didn't exist.

**R13's test doesn't run the train.** It drives `gate --land` and `land-verdicts`, not `train --run`. It shows that no attempt is written and the next step is still `gate`; that `train --run` then stops rests on `_run_loop`'s existing `problem` rule.

## Changes to `plan.md`
I wrote the plan first, then added four sections where the build departed from it:
- **Status splits the park line in two.** Two full timestamps don't fit `status`'s width, so it prints `⏸ parked on …, held by …;` and the retry and deadline on the line under it. The board keeps one line.
- **The `parked` stop's next step doesn't offer `/sdlc:ship`,** and the pinned test now exempts it.
- **Where the code landed:** `park_problem()` is in `run_state.py`; `busy_line()` and `_gate_busy()` sit above `cmd_gate`.
- **Mark, then cut.** The plan's own call, kept: `busy_of()` replaces paths and terms with placeholders first and cuts to 200 characters after.

Nothing is left in `notes.md`.

- UNTESTABLE: R18: the wording of the `REFERENCE.md` and README prose has to be read by a reviewer; the feature-map entry and the states table have tests.

- DECISION: [default] Keep the `AGENTS.md` edit to the `verdicts` sentence (it now also reads the vouched `runs/parked.md`, and the clock for a park), worded as the approved spec's *Contracts touched* says. Going ahead with it unless told otherwise.
  - OPTION: keep it — the map matches the code; the rule's intent (vouched, deadline from the base branch, clock injected) is said beside it
  - OPTION: revert the sentence — the map would say `verdicts` reads no park, which the code now does
  - WHY: the spec flags this sentence as a policy edit for your yes, and approving the spec looked like that yes
- DECISION: [default] Should `factory.py check` catch the output only when `[park] exit` is set, printing it once the command ends? Going ahead with that.
  - OPTION: catch only with `[park] exit` set — the payload can be read; a host without the key sees no change
  - OPTION: never catch — output streams as now, but `busy:` always reads `unknown held by unknown`
  - OPTION: tee the output — it streams and is read, but needs threads around the one place a host's command runs
  - WHY: the spec leaves this to the plan, and R1 says a host without the key sees no change
- DECISION: [default] Should `status` print the park's line in two, split at its `; `? Going ahead with two lines.
  - OPTION: two lines — the full retry and deadline stay visible at `status`'s width
  - OPTION: one line, cut — matches R16's wording, but `_cut()` drops the deadline
  - WHY: the deadline is the part the person needs to see
- DECISION: [default] Should the `parked` stop's next step offer no `/sdlc:ship` alternative, unlike the other ways? Going ahead with none.
  - OPTION: none — matches R9's wording exactly
  - OPTION: add `, or /sdlc:ship {id}` — consistent with the other ways, but shipping by hand meets the same busy check
  - WHY: R9 fixes the line's form

## Evidence

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 222 > /tmp/park222/check.log 2>&1; tail -25 /tmp/park222/check.log
FAILED tests/test_factory_loop.py::test_config_defaults_and_its_warnings - As...
FAILED tests/test_factory_loop.py::test_each_way_on_fits_two_lines_at_phone_width
FAILED tests/test_board.py::test_status_records_only_gain_keys - AssertionErr...
FAILED tests/test_registry.py::test_each_command_sits_beside_its_handler[factory]
FAILED tests/test_feature_map.py::test_agents_md_fits_100_columns - assert [3...
FAILED tests/test_suite_shape.py::test_no_test_takes_a_fixture_it_never_uses
6 failed, 3974 passed, 29 skipped in 281.98s (0:04:41)
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_factory_loop.py tests/test_board.py tests/test_registry.py tests/test_feature_map.py tests/test_suite_shape.py tests/test_factory_park.py
FAILED tests/test_feature_map.py::test_agents_md_fits_100_columns - assert [3...
1 failed, 430 passed, 28 skipped in 23.68s
exit: 1

$ uv run --group dev pytest -q tests/test_feature_map.py
9 passed in 0.20s
exit: 0

$ uv run --group dev ruff check . --output-format concise
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
342 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 222 > /tmp/park222/check2.log 2>&1; grep -E "passed|failed" /tmp/park222/check2.log | tail -3
3980 passed, 29 skipped in 247.01s (0:04:07)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_factory_park.py tests/test_autopilot.py tests/test_land.py -k "park or busy"
23 passed, 152 deselected in 11.36s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_park.py -k "check_passes_busy"   # with `catch = False` patched in, then restored
FAILED tests/test_factory_park.py::test_check_passes_busy_through_and_writes_nothing
1 failed, 17 deselected in 0.52s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_park.py -k "check_passes_busy or slot_wait"   # restored
3 passed, 15 deselected in 2.60s
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py -k waits_out_a_park   # against HEAD's autopilot.py
E       AttributeError: <module 'factory_autopilot' …> has no attribute '_pause'
1 failed, 54 deselected in 0.27s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py -n auto   # restored
55 passed in 9.34s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -n auto
491 passed in 27.73s
exit: 0

$ uv run --group dev pytest -q tests/test_feature_map.py -k vocabulary   # before the FEATURES.md entry
FAILED tests/test_feature_map.py::test_every_vocabulary_term_has_an_entry - A...
1 failed, 8 deselected in 0.08s
exit: 1

$ git status --short; git log --oneline -1
 M AGENTS.md … ?? .sdlc/work/222-parked-changes/ ?? tests/test_factory_park.py
3bafdfd Close 216-autopilot
exit: 0
