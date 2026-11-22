I built the change: a card being mended now stays in Building with a `mending <role>` step, and `status` no longer lists it under Needs you. A `mend` stop reaches Needs you only once the role's one mend is used up or the mend has gone past the agent's timeout. It is a Tier 1 change, but its Approach touches five files, so I wrote `plan.md` first. The work is uncommitted.

Every new test failed first for the reason I expected, then passed. The touched test files pass (670 passed, 28 skipped), as do the related `needs_of()` tests (27 passed) and ruff. I also ran the full gate through `factory.py check 233`. Its output was cut to the last 15 lines, so I don't have its pytest count; it did reach both `claude plugin validate --strict` steps, and since `check.sh` stops at the first failure, ruff and the whole suite must have passed. `build/round-1.gate.md` will hold the gate's own record.

## Slices built
1. **The record.** `runs/step.md` gets a `ROLE:` line, written by `step_text()` and read back by `read_step()`, with matching copies in `factory.py` and `factory_records.py`. A new `factory_records.mending(folder)` returns the role, round and start time of a mend the step record names, plus its deadline: the start time plus `AGENT_TIMEOUT`.
2. **The factory records the mend.** `agent --task mend` writes `STEP: mend`, its round, `ROLE:` and `SINCE:` before the session starts, keeping the last reading's limit, reviewers and depth. A refused mend writes nothing. A mend whose session fails puts the record back as it was (`_unrecord_mend()`), so a card never says "mending" while nothing runs. `runs/stopped.md` is still written only by `verdicts --record`.
3. **The rule.** `sdlc.mend_running(rec)` is true only while the stop's way is `mend`, a mend is recorded and the time is before its deadline. While it is true, `needs_of()` names no need for the stop. Past the deadline the need reads: `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build <id> if no session runs it`, with no comma.
4. **The readers.**
   - **Board:** a card being mended shows the build track at the mended role's step (the builder at `build`, or `rework` after round 1; the arbiter at `arbitrate`; the approver at `approve`; a reviewer at `review`). That step is labelled `mending <role>`, with elapsed time and no typical-time figure. Its next step reads "the factory is mending the <role>: wait for it…", and the stop's problems are flagged `mending:` instead of `stopped:`.
   - **`status`:** marks the change `mending, ` and lists it under Building with a `→` line saying the same.
   - **Docs:** the factory README's `stop` row and `runs/step.md` line, the step-track paragraph in `docs/REFERENCE.md`, and the docstrings that say who writes `runs/step.md`.

## Tests added
- `tests/test_board.py::test_the_step_record_is_a_pinned_copy` (extended): `ROLE_RE` and a mend record read the same in both copies.
- `tests/test_board.py::test_a_mend_step_reads_with_its_deadline`: `mending()` returns the deadline, and returns None for any other step, a record with no start time, or no record.
- `tests/test_factory_agent.py::test_a_mend_records_its_step_before_its_session_runs`: the record is written before the session runs, with nothing written for a refused mend.
- `tests/test_factory_agent.py::test_a_failed_mend_puts_the_step_record_back`.
- `tests/test_sdlc.py::test_a_mend_under_way_needs_nobody_until_its_timeout`: drives `needs_of()` through all three cases (mend under way, mend used up, mend past its timeout), plus a stop with no mend recorded or no clock.
- `tests/test_board.py::test_a_card_being_mended_is_building_with_a_mending_step`: the same three cases on the board's card and step track.
- `tests/test_board.py::test_status_lists_a_change_being_mended_under_building`: under a mend the change is in Building, and in Needs you once the mend is past its timeout.
- `tests/test_modules.py`: `ROLE_RE` and `mending` are listed among the pinned record names, and `mend_running` among core's own rules. `test_status_records_only_gain_keys` now allows the two new keys (`mending`, `mend_running`).

## Changes to `plan.md`
While building I added three things the first draft didn't have: the restore after a failed mend, the `mending:` flag in `board.html`, and the doc lines. The agent tests went to `tests/test_factory_agent.py`, where the other mend tests are. `plan.md` now says all of this.

## `notes.md`
It records the two defaults below, explains why "newer than the stop" comes from the order the records are written in rather than from file times, and records the failed-mend restore. No unticked lines.

- DECISION: [default] Is the timeout before an unmended `mend` stop becomes the person's the agent's own? Going ahead with `AGENT_TIMEOUT` (3 hours) unless told otherwise.
  - OPTION: `AGENT_TIMEOUT` — no session can outlive it, so a mend past it is surely dead; a crashed supervisor's card waits up to 3 hours
  - OPTION: a fixed shorter figure (say 30 minutes) — a dead mend surfaces sooner; a slow live mend could show under Needs you while it still runs
  - WHY: the intent's constraint that only files and their times decide, and the agent's timeout is the one bound a session can't pass
- DECISION: [default] Does `agent --task mend` record the mend in `runs/step.md` (with a new `ROLE:` line), not read it from `runs/mended` and the stop's time? Going ahead with `runs/step.md` unless told otherwise.
  - OPTION: `runs/step.md` with `ROLE:` — the card changes the moment the mend starts; the step record gains one optional line
  - OPTION: `runs/mended` plus the stop's time — no new line; `runs/mended` is written only after the reply, so the card would still show Needs you during the mend
  - WHY: the intent's outcome that the card changes when the supervisor acts, not after the reply

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_board.py::test_the_step_record_is_a_pinned_copy
FAILED tests/test_board.py::test_the_step_record_is_a_pinned_copy - Attribute...
1 failed in 0.89s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py::test_the_step_record_is_a_pinned_copy
1 passed in 0.20s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py::test_a_mend_step_reads_with_its_deadline tests/test_modules.py
FAILED tests/test_board.py::test_a_mend_step_reads_with_its_deadline - Attrib...
FAILED tests/test_modules.py::test_the_record_readers_live_in_factory_records
2 failed, 45 passed in 9.63s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py::test_a_mend_step_reads_with_its_deadline tests/test_modules.py
47 passed in 91.76s (0:01:31)
exit: 0

$ uv run --group dev pytest -q tests/test_factory_agent.py::test_a_mend_records_its_step_before_its_session_runs
E       assert ('stop', None, None) == ('mend', 1, 'builder')
1 failed in 3.38s
exit: 1

$ uv run --group dev pytest -q tests/test_factory_agent.py -k mend
9 passed, 93 deselected in 33.46s
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py::test_a_mend_under_way_needs_nobody_until_its_timeout
E       AssertionError: assert (['stopped: re... agent again'] == []
exit: 1

$ uv run --group dev pytest -q tests/test_sdlc.py -k "needs or stop or park or mend"
27 passed, 270 deselected in 5.32s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k "mended or being_mended"
E       AssertionError: ['stopped: rerun to ask an agent again']
E       AssertionError: /private/var/folders/.../repo/.sdlc/work — 5 open, 6 total   today: 2026-11-22
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k being_mended
2 passed, 323 deselected in 6.61s
exit: 0

$ uv run --group dev pytest -q tests/test_factory_agent.py::test_a_failed_mend_puts_the_step_record_back
E       AssertionError: assert 'STEP: mend\n...LE: builder\n' == 'STEP: stop\n...1T00:00:00Z\n'
exit: 1

$ uv run --group dev pytest -q tests/test_factory_agent.py -k mend
10 passed, 93 deselected in 30.79s
exit: 0

$ uv run --group dev ruff check plugins scripts tests -q
(no output)
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_board.py tests/test_modules.py tests/test_factory_agent.py tests/test_factory_loop.py tests/test_windows.py tests/test_factory_park.py
670 passed, 28 skipped in 186.21s (0:03:06)
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py -k "needs or stop or park or mend"
27 passed, 270 deselected in 12.47s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 233 2>&1 | tail -15; echo "exit: $?"
✔ Validation passed
(…factory plugin directory warning: ICON_MISSING…)
✔ Validation passed
exit: 0
(the printed exit is `tail`'s; reaching both validate steps under `check.sh`'s `set -euo pipefail` means ruff, the format check and the suite passed, but the pytest count was cut off by `tail`)

$ cat check.sh
set -euo pipefail … ruff check, ruff format --check, pytest -q -n auto, claude plugin validate --strict . and plugins/factory
exit: 0
