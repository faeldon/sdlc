I built all four fixes from the 110 review seeds. The changes are uncommitted in the worktree and nothing was committed. The gate passes: 2252 passed, 13 skipped.

The prompt called this a Tier 2 change, but `intent.md` says `tier: 1`. I still wrote `plan.md` because the change touches more than a couple of files.

## Slices built

1. **Long tokens wrap (seed 81):** `.next code` in `scripts/board.html` now has `overflow-wrap: anywhere`, like `.title`, `.needs` and `.flag` already do.
2. **A stop's next step is short (seed 82):** in `factory.py`, each `WAYS` line is now just the command and a few words, 90 characters at most. Examples:
   - `rerun /sdlc-factory:build {id}, or /sdlc:ship {id}`
   - `fix its cause, then /sdlc-factory:build {id}, or /sdlc:ship {id}`

   The longer explanations moved to a new `WAYS_WHY`, which `stop_text()` writes into the body of `runs/stopped.md`, between `NEXT:` and the problems. The board's drawer already lists that file. The new line matches none of `STOPPED_RE`, `NEXT_RE` or `PROBLEM_RE`, so `factory_stop()` and the board read the record exactly as before.
3. **Plain needs-you wording (seed 84):** a new `FACTORY_STOP_NEEDS` in `sdlc.py` gives each way an instruction in plain words, so the bare word `mend` never shows:
   - `stopped: review an agent's commit`
   - `stopped: rerun to ask an agent again`
   - `stopped: fix its cause and rerun`

   A record that won't read still says `stopped: read runs/stopped.md`.
4. **The stop test is parenthesised (seed 83):** `_progress()` now reads `entry.get("stopped") or ((folder / STOPPED).is_file() and entry["stage"] == "build")`. Its result is the same as before.

I also updated three docs to match: `docs/REFERENCE.md`, the example in `skills/status/SKILL.md`, and the `runs/stopped.md` description in `plugins/factory/README.md`.

## Tests added
- `test_a_long_next_step_wraps_inside_its_card` (test_board.py): the wrap rule (seed 81).
- `test_each_way_on_fits_two_lines_at_phone_width` (test_factory.py): each `NEXT:` fits two lines at 390px and still names its command (seed 82).
- `test_the_stop_record_says_why_and_reads_as_before` (test_board.py): the longer text is in the record, and `factory_stop()` reads the same fields (seed 82).
- `test_a_stop_hides_the_step_track_as_it_always_has` (test_board.py): pins the stop test's result (seed 83). It passed before the edit, as it should for a change that only adds parentheses. No test can see the parentheses themselves, so `checks.md` has a grep for them.
- `test_a_stop_s_need_is_in_plain_words`, plus `test_a_stop_needs_its_way_on` reworked (test_sdlc.py): the plain wording (seed 84). `test_a_blocking_decision_needs_its_id` and `test_status_ends_with_what_needs_me` were updated to the new wording.

## plan.md and notes.md
- **`plan.md`:** the test list now uses the names the tests were actually given, and says that the parentheses are proved by the check in `checks.md`.
- **`notes.md`:** nothing left there.

## Decisions
- DECISION: [default] Shorten the stop wording in `factory.py`'s `WAYS` itself, not just in how the board shows it? This is the intent's open question. Options: change `WAYS`; change only the board. Going ahead with changing `WAYS`, as the Approach says: `status`'s `→` line and the board both show it, and one short text keeps them in step. It may conflict with 112, 113 or 119 when they land, but only in the small `WAYS` block.
- DECISION: [default] Word a stop's need as `stopped: <instruction>` rather than the intent's example `stopped, an agent asked again`? Going ahead with the colon form. `status` separates a change's needs with `, `, so a comma inside one need would split it. And every other need is already an instruction (`decide D1`, `approve its spec`).

## Evidence

$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_factory.py tests/test_sdlc.py -k "way_on or plain_words or blocking_decision_needs or what_needs_me or says_why or wraps_inside or hides_the_step_track or fits_two_lines"   (red, before the code)
FAILED tests/test_board.py::test_a_long_next_step_wraps_inside_its_card - Ass...
FAILED tests/test_board.py::test_the_stop_record_says_why_and_reads_as_before
FAILED tests/test_sdlc.py::test_a_stop_needs_its_way_on - AssertionError: ass...
FAILED tests/test_sdlc.py::test_a_stop_s_need_is_in_plain_words - AssertionEr...
FAILED tests/test_sdlc.py::test_a_blocking_decision_needs_its_id - AssertionE...
FAILED tests/test_factory.py::test_each_way_on_fits_two_lines_at_phone_width
FAILED tests/test_board.py::test_status_ends_with_what_needs_me - AssertionEr...
7 failed, 1 passed in 1.72s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_factory.py tests/test_sdlc.py tests/test_metrics.py
681 passed, 13 skipped in 19.98s
exit: 0

$ sh -c "<checks.md's one sh block>"
exit: 0

$ ./check.sh
All checks passed!
2252 passed, 13 skipped in 191.40s (0:03:11)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_board.py tests/test_factory.py tests/test_sdlc.py -k "says_why or wraps_inside or hides_the_step_track or fits_two_lines or way_on or plain_words or blocking_decision_needs or what_needs_me"
8 passed, 568 deselected, 1 warning in 30.10s
exit: 0
