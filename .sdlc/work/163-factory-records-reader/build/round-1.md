I built it: core now reads every factory record through one module, `scripts/factory_records.py`. The full gate passes and `status --all` prints the same bytes as the base branch's script on this repo. Everything is uncommitted and no decisions are raised.

**What moved where**
- **New module:** `scripts/factory_records.py` now holds every copy of the factory's record parsing. Before, those copies were spread across `sdlc.py`, `board.py` and `closing.py`. The module uses `factory.py`'s names and is pure: no subprocess, no `sdlc`, and nothing runs at load but definitions. It also adds a few names so no other file spells a record's file name: `DECISION_FILE`, `LEDGER_FILE`, `BUILDER_SESSIONS`, `SESSIONS`, `gate_kind()` and `gate_seconds()`.
- **`sdlc.py`** loads the module once, beside `_load_metrics()`, and binds nothing into it. Its copies are gone and every caller reads `factory_records.<name>`. `_hand_main(root)` keeps the one `git worktree list` call. The rules over the records stay in `sdlc.py`: `needs_of`, `column`, `seen_stage`, `answered`, `decide_step`, `FACTORY_STOP_NEEDS`, and the hand gate's runner and writer.
- **`board.py`** lost its copies and reads `sdlc.factory_records.<name>`. `history_samples` keeps its own git walk and only uses `gate_kind()` and `gate_seconds()` from the module.
- **`closing.py`**: `_factory_files`, `_agent_sessions` and `_agent_models` keep their signatures (R9). They now pass `show`/`listing` callables from a new `_branch_files()` to the module, so the git reads stay in close and the parsing is the module's.
- **`AGENTS.md`** (*Modules loaded by path*, *The board*, *The factory*) and the docstrings of `board.py` and `closing.py` now point to the module (R11).

**Tests added** (`tests/test_modules.py`), all seen failing first because the module didn't exist:
- `test_factory_records_is_pure_and_loaded_once` (R1)
- `test_the_board_and_close_read_records_through_sdlc` (R2)
- `test_the_record_readers_live_in_factory_records` (R3, R4)
- `test_no_factory_record_is_named_outside_its_reader` (R5). It first shows its own checker catching `(folder / "decision.md")` and an f-string piece.
- `test_every_shared_name_is_the_factorys` (R6)

The existing pins now compare the module with `factory.py` (R7). Otherwise the only test edits change where a test reads a moved name, plus ruff's rewrapping (R8). Two tests lost a pin each:
- **The two `opening` pins are now one.** I kept `test_board.py::test_the_boards_opening_is_a_pinned_copy` and removed `test_metrics.py::test_sdlcs_opening_is_a_pinned_copy_of_the_factorys`.
- **One line is gone from `test_the_landing_stop_is_read_as_status_reads_it`.** It pinned `sdlc.FACTORY_LAND_STOPS == board.LAND_STOPS`, and with one copy it would only compare the module with itself.

**Changes to `plan.md`** (written before any code; its "as built" notes record these):
- **Callables are folder-relative.** The module's `show`/`listing` take paths relative to the change's folder, so `run_counts`, `session_roles` and `session_models` take no `folder` argument, unlike the spec's signatures.
- **One name is allowed by hand.** R3's test exempts `sdlc.py`'s own `MOVES_RE`, which reads the direction doc's `**Moves O<n>:**` line, not a landing record.
- **New gate-list keys.** `history_samples` keys its gate lists `round`/`land` instead of `round-`/`land-`.

Nothing was left in `notes.md`.

**Named tests run:** `tests/test_modules.py` (18 passed) and the six pin-holding files together (1287 passed, 28 skipped). The full gate went through `factory.py check 163`.

## Evidence

$ uv run --group dev pytest -q tests/test_modules.py   (before the module existed)
FAILED tests/test_modules.py::test_factory_records_is_pure_and_loaded_once - ...
FAILED tests/test_modules.py::test_the_board_and_close_read_records_through_sdlc
FAILED tests/test_modules.py::test_the_record_readers_live_in_factory_records
FAILED tests/test_modules.py::test_no_factory_record_is_named_outside_its_reader
FAILED tests/test_modules.py::test_every_shared_name_is_the_factorys - FileNo...
5 failed, 13 passed in 2.11s
exit: 1

$ uv run --group dev pytest -q tests/test_modules.py
18 passed in 1.59s
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_modules.py tests/test_board.py tests/test_hand_gate.py tests/test_metrics.py tests/test_archive.py tests/test_sdlc.py tests/test_factory.py
1287 passed, 28 skipped in 81.65s (0:01:21)
exit: 0

$ uv run --group dev ruff check scripts tests --output-format concise
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
291 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 163 > /tmp/b163/check.log 2>&1; echo "exit: $?"; grep -E "passed|failed|error" /tmp/b163/check.log | grep -v "Validation\|warning" | tail -5
All checks passed!
2964 passed, 28 skipped in 137.21s (0:02:17)
exit: 0

$ uv run --quiet --script /tmp/b163/base/scripts/sdlc.py status --all > /tmp/b163/before.txt   (the base commit 1932f73's scripts)
exit: 0

$ uv run --quiet --script scripts/sdlc.py status --all > /tmp/b163/after.txt
exit: 0

$ diff /tmp/b163/before.txt /tmp/b163/after.txt
(no output)
exit: 0
