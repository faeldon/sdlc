Built all fourteen requirements in four slices. The change is uncommitted and `sdlc.py` is untouched. The full gate passed: ruff, format, 3062 tests and plugin validate.

**Slices**
1. **Repo identity (R1–R5).** `board.py` now has `_repo_id(home)`: the first 16 hex characters of the SHA-256 of the main checkout's resolved POSIX path. `/state.json` sends it as `repo_id`. `_is_board()` became `_board_on()`, which returns the parsed payload. `cmd_board()` now answers `already` only when the board on the port shows this repo (its `repo_id` matches). A board showing another repo, or one with no `repo_id`, gets `port N holds another repo's board: pass --port <N>`. Anything else on the port gets the same refusal as before.
2. **The run lock (R7–R10, R12, R13).** `board.py` gains a copy of `TRAIN_RUN_LOCK`, plus `train_run_held(home)`, `_release(fd)` and `_mark_unattended()`.
   - The board opens the lock file `O_RDONLY` and never creates it. It tries the lock with `sdlc._try_lock` and lets go at once.
   - It only tries the lock when some landing card is in a train and not stopped, and then once per `/state.json`.
   - `_land_progress()` sets `"unattended": False` by default, so every landing card has the same shape.
3. **The page (R11).** `progressRow()` shows `running unattended: train --run takes each step` when `p.unattended` is true, built with `h()`.
4. **The skill and docs (R6, R14).** I reworded Step 1 of the dashboard skill; the command and its `allowed-tools` rule are unchanged. I also updated `board.py`'s docstring, REFERENCE.md's *The board*, and AGENTS.md: *The factory*'s list now includes "the train's run lock, for the board", and *The board* paragraph covers both changes.

**Tests added** (`tests/test_board.py`, all `portable`)
- R1 `test_the_board_names_its_repo_by_id_not_by_path`: the id is the same from a worktree, differs for another repo, and no path appears in the body.
- R3 `test_another_repos_board_is_a_refusal`: two repos' boards; the second is refused, and the first repo still gets `already`.
- R4 `test_a_board_that_names_no_repo_is_a_refusal`: a stand-in old board is refused.
- R7 `test_a_held_run_lock_marks_a_train_card_unattended`: with the lock held, the train card reads true; an ejected card and a card outside a train read false; it goes back to false once the lock is released.
- R8 `test_land_step_alone_never_claims_a_live_loop`: false with the lock file missing, and false when the file exists but is free.
- R9 `test_reading_the_run_lock_creates_nothing_and_holds_nothing`
- R10 `test_no_train_no_lock_probe`: no probe without a live train card, and one probe per read when there is one.
- R11 `test_the_page_says_unattended_only_from_the_lock`
- R12 `test_the_run_lock_name_is_a_pinned_copy`
- R6 `test_the_dashboard_skill_offers_another_port_on_a_refusal`
- R13: `test_the_board_writes_nothing` now adds a train card under way and compares a listing of the git common dir before and after.
- R2 and R5: `test_a_second_board_reports_the_first_and_anything_else_is_refused` is unchanged and still passes.

**Red first:** R1, R3, R4, R6, R7, R8, R10, R11 and R12 each failed for the expected reason before the code went in. Two tests passed before any probe existed, so they never showed red: R9's test and the R13 extension. They guard against a probe that creates the lock file or keeps hold of it.

**`plan.md`:** I wrote it before the code. The only change since is that it now names `_mark_unattended()`. Nothing went into `notes.md`.

**Approved departure from the intent:** when the lock is free, the board does take it for the span of two syscalls; it never takes it while a loop holds it. The spec flagged this, and the intent marks the open question resolved with the spec's approval.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k "names_its_repo or another_repos_board or names_no_repo or second_board_reports"   (before the code)
3 failed, 1 passed, 299 deselected in 3.32s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "names_its_repo or another_repos_board or names_no_repo or second_board_reports"
4 passed, 299 deselected in 10.59s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k "unattended or live_loop or creates_nothing or no_lock_probe or pinned_copy or writes_nothing"   (before the code)
5 failed, 6 passed, 298 deselected in 2.73s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k "unattended or live_loop or creates_nothing or no_lock_probe or pinned_copy or writes_nothing"
11 passed, 298 deselected in 3.87s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -k offers_another_port   (before the skill edit)
1 failed, 309 deselected in 0.24s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py -k offers_another_port
1 passed, 309 deselected in 0.04s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -n auto
415 passed in 0.93s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_modules.py tests/test_skills.py tests/test_windows.py tests/test_nothing_local.py
765 passed, 28 skipped in 9.10s
exit: 0

$ uv run --group dev pytest -q -m portable tests/test_board.py
266 passed, 28 skipped, 16 deselected in 39.79s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 167
All checks passed!
307 files already formatted
3062 passed, 28 skipped in 117.97s (0:01:57)
✔ Validation passed
exit: 0
