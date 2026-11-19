---
id: 167
slug: board-knows-its-repo
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 167 — The board knows which repo it shows, and when a landing runs unattended · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code:

- A board's repo is `sdlc.main_root(root)`: `state()` already calls it `home`, and it gives the same answer from the main checkout and from every worktree.
- A train's run lock is `TRAIN_RUN_LOCK = "sdlc-factory-train-run.lock"` in the git common dir. The loop holds it with `flock(LOCK_EX)`, or `msvcrt.locking` on Windows, for its whole life, through an open descriptor (`landing.py`, `run_lock()`). The loop writes nothing into the file.
- The factory's own `train_running()` tells whether a loop is live by trying the lock without waiting. So do `--begin`, `--eject` and `--stop` before they act (`landing.py:1619`).
- A train only exists with a train state, and `_train_run()` refuses without one. Every change in a train has `TRAIN: k of n` in its `runs/land-step.md` (`_record_land()`). So any card a loop is landing has `progress.train` set.
- The page polls `/state.json` every 2 s (`POLL_MS`). It redraws only when `st.changes` changes (`render()`'s key).
- A running board reloads `board.py` from disk but keeps the `sdlc.py` it started with in memory.

1. **R1.** `/state.json` carries `repo_id`: the first 16 hex characters of the SHA-256 of `main_root(root).resolve().as_posix()`.
   - It is the same for a board started from the main checkout and one started from a worktree of the same repo.
   - It differs between two repos.
   - The payload holds no absolute path.
   - `test_the_board_names_its_repo_by_id_not_by_path` fails if two fixture repos share an id, if a worktree's id differs from its main checkout's, or if `str(home)` appears in the body.
2. **R2.** `sdlc.py board --port N`, on a port held by a board whose `repo_id` matches this repo's, still prints `{"url": …, "serving": "already"}` and exits 0. `test_a_second_board_reports_the_first_and_anything_else_is_refused` keeps passing unchanged.
3. **R3.** On a port held by another repo's board, `board` exits 1 and prints a refusal that names the port and says it shows another repo's board, e.g. `port 5170 holds another repo's board: pass --port <N>`. It never prints `already`. `test_another_repos_board_is_a_refusal` starts two fixture repos' boards and fails if the second reports `already`.
4. **R4.** A board that answers `"board": "sdlc"` with no `repo_id` (one started from an older plugin copy) is refused the same way as R3, never reported as `already`. `test_a_board_that_names_no_repo_is_a_refusal` serves a stand-in `state.json` and fails on `already`.
5. **R5.** Anything on the port that isn't a board is refused with today's text, and `test_a_second_board_reports_the_first_and_anything_else_is_refused` keeps checking it.
6. **R6.** `skills/dashboard/SKILL.md`, Step 1, says three things:
   - `"serving": "already"` means this repo's board already holds the port, and it is the one to open.
   - A refusal means another repo's board, or something else, holds the port. The skill says which, and runs the same command again with another `--port` (e.g. 5171).
   - The command and its `allowed-tools` rule don't change. `tests/test_skills.py` keeps passing, and `test_the_dashboard_skill_offers_another_port_on_a_refusal` fails if the text stops saying both.
7. **R7.** A landing card's `progress` gains `unattended`. It is `true` only when all three hold: the card is in a train (`train` set), it isn't stopped, and another process holds the run lock when `/state.json` is built. Otherwise it is `false`. `test_a_held_run_lock_marks_a_train_card_unattended` takes the lock on its own descriptor and fails unless the train card reads `true`. The same test checks that a stopped or ejected card, and a card not in a train, read `false`.
8. **R8.** If the run lock is free or doesn't exist, `unattended` is `false`, even when a train card's `land-step.md` names a step in flight. That is the case of a loop that died mid-step, or steps run by hand. `test_land_step_alone_never_claims_a_live_loop` fails if it reads `true`.
9. **R9.** Reading the lock leaves nothing behind:
   - A missing lock file stays missing. The board opens the file read-only, with no `O_CREAT`.
   - A free lock is free again before `state()` returns.
   - `test_reading_the_run_lock_creates_nothing_and_holds_nothing` fails if the file appears after `state()`, or if the test can't take the lock right after `state()`.
10. **R10.** The board tries the lock only while some card is a train member that isn't stopped, so with no train under way it never touches the lock. `test_no_train_no_lock_probe` swaps in a stand-in for the probe and fails if it is called.
11. **R11.** The page shows `running unattended: train --run takes each step` on a landing card when `p.unattended` is true, built with `h()`/`textContent`, and nothing about a loop otherwise. `test_the_page_says_unattended_only_from_the_lock` reads `progressRow` in `board.html` and fails if the text is shown on any other condition.
12. **R12.** `board.py`'s copy of `TRAIN_RUN_LOCK` equals `landing.py`'s. `test_the_run_lock_name_is_a_pinned_copy` loads `landing.py` through `factory.py` and fails on drift.
13. **R13.** The board still writes nothing and serves `127.0.0.1` alone. The existing `test_the_board_writes_nothing` and `test_the_board_answers_three_gets_and_nothing_else` pass, and `test_the_board_writes_nothing` also compares a listing of the git common dir before and after its requests, so a created lock file fails it.
14. **R14.** The docs say the same as the code:
   - `board.py`'s docstring.
   - REFERENCE.md, *The board*: a second `board` on a port that another repo's board holds is refused, and a train card says when `train --run` is taking its steps.
   - AGENTS.md: *The factory*'s list of the factory's files that `sdlc` reads gains "the train's run lock, for the board", and *The board* paragraph mentions it.

## Design

**Repo identity (R1–R5).** `board.py` gains `_repo_id(home) -> str`, which hashes `home.resolve().as_posix()`. `state()` adds `"repo_id": _repo_id(home)` next to the `repo` it already sends. The page keeps showing `repo`, the folder name, so it doesn't change.

`_is_board(port)` becomes `_board_on(port) -> dict | None`, which returns the parsed `state.json` or None, catching the same exceptions it catches today. `cmd_board(root, port)`, after the bind fails, decides as follows:

- `found is None`: today's refusal (R5).
- `found.get("board") != MARKER`: today's refusal (R5).
- `found.get("repo_id") != _repo_id(sdlc.main_root(root))`: the other-repo refusal (R3, R4).
- Otherwise: `already` (R2).

Both sides of the comparison come from the same function on the same kind of input (git's main root, resolved, as POSIX). REVIEW.md warns about comparing paths that two sources write differently; this avoids it.

**The run lock (R7–R10, R12).** Everything is in `board.py`:

- `TRAIN_RUN_LOCK`, a copy of the lock's file name, pinned by R12.
- `_release(fd)`, the factory's `_unlock()`: `msvcrt.LK_UNLCK` on Windows, imported inside the function, and nothing elsewhere, where closing the descriptor drops a flock.
- `train_run_held(home) -> bool`. It works in five steps:
  1. Find the common dir with `sdlc._git(home, "rev-parse", "--path-format=absolute", "--git-common-dir")`. None means not held.
  2. Call `os.open(path, os.O_RDONLY)`. `FileNotFoundError` means not held.
  3. Call `sdlc._try_lock(fd)`. False means held.
  4. If it got the lock, `_release(fd)` at once.
  5. Close the descriptor in a `finally`.

  Any other `OSError` reads as not held, so the board never claims a loop it can't see.

In `state()`, the board builds the entries first. If any entry's `progress` is a landing (`kind == "land"`) with `train` set and `stopped` false, it calls `train_run_held(home)` once. It then sets `progress["unattended"]` on each landing progress by R7's rule. Every other landing progress gets `false`. `_land_progress()` returns `"unattended": False` by default, so the card's shape is the same whether or not the board tried the lock.

`unattended` lives on each card, not at the top of `state.json`. `render()`'s redraw key is `st.changes`, so a top-level flag wouldn't redraw the page when the loop starts or ends.

**Why the code stays in `board.py`.** `sdlc.py` is untouched. A board that is already running reloads `board.py` but keeps its old `sdlc.py`. A new name in `sdlc.py` would turn every `/state.json` into an `AttributeError` until the board restarts. Only existing names are used: `sdlc._try_lock`, `sdlc._git` and `sdlc.main_root`.

**The page (R11).** `progressRow()` adds `if (land && p.unattended) parts.push(h("div", { class: "meta" }, "running unattended: train --run takes each step"))`. The step's existing `running` meta stays as it is: it means the step has no typical time, not that a loop is live.

**The skill (R6).** Step 1's paragraph on the first output line is reworded as R6 says. The bash block and `allowed-tools` don't change.

**Edge cases.**

- A board from an older plugin copy holding 5170 is refused (R4). The person passes `--port`, or stops the old one.
- A train card in Needs you because its landing stopped has `stopped` true, so it is never unattended.
- On Windows, `msvcrt.locking` on a read-only handle: if it raises anything but "held", R8's "not held" answer applies. The tests that hold the lock are marked `portable`.

## Contracts touched

- **The board writes nothing and serves `127.0.0.1` alone** (AGENTS.md, *The board*). The bind, the Host check and the GET-only handler don't change.
  - The lock file is opened read-only with no `O_CREAT`, so the board never creates it.
  - An advisory lock taken and released in the same call writes nothing to disk.
  - R13 extends the "writes nothing" test to the git common dir, where `git status` can't see.
- **The board loads only when `board` runs, and never imports or runs `factory.py`.** The board copies one constant, as it copies every other factory name, and pins it by a test. It loads nothing new.
- **163: core reads a run's records only through `factory_records.py`.** The rule covers the files a run leaves in a change's folder. `factory_records.py` is pure: no git, and nothing done but parsing text. The run lock is neither of those. It sits in the git common dir and is read by taking an OS lock, which makes it the same kind of thing as the gate slots' lock files. Core already holds the slots' copies (`SLOT_NAME`, `_try_lock`) outside `factory_records`, under `CONSUMER_NAMES`. `RECORD_FILES` doesn't name the lock, and this change leaves that list alone.
- **AGENTS.md, *The factory*: what `sdlc` reads of the factory's files.** The list grows by "the train's run lock, for the board". The intent names this. It is a policy-doc edit made on purpose, in this change (R14), not a side effect.
- **The scripts run on Windows.** `msvcrt` is imported only inside `_release()`. There is no new subprocess, and the tests that hold the lock are `portable`.
- **Nothing local** (`tests/test_nothing_local.py`). Tests use `tmp_path` repos and never write a home path. The `repo_id` design keeps any path out of the payload.
- **The intent's constraint "Reading the lock must not take it" is not met as written.** Python offers no portable way to test an flock or an `msvcrt` lock without trying it. The design takes the lock for the span of two syscalls when it is free. It never takes it while a loop holds it, so a running loop never sees the board.
  - Risk: a `train --run`, `--begin`, `--eject` or `--stop` started in that same instant is refused with "a train --run is under way" and works on a rerun.
  - The factory's own `train_running()` already carries this risk between its commands, and R10 limits the board's tries to while a train is under way.
  - **This needs the person's yes.** The alternative is the pid record under *Alternatives rejected*.

## Alternatives rejected

- **The main checkout's absolute path in `state.json`.** It compares just as well, but it puts a home path in a payload the page never shows, which this repo keeps out everywhere it can. A hash says "same repo or not" and nothing more.
- **Comparing `repo` (the folder name).** Two clones, or two unrelated repos with the same folder name, would match, which is the bug again.
- **The loop writes its pid into the lock file, and the board checks that the pid is alive without taking the lock.** This meets the constraint to the letter, but:
  - It is a factory change in `landing.py`.
  - A dead loop's pid can be reused by another process.
  - Checking a pid on Windows needs `ctypes`/`OpenProcess`, because `os.kill(pid, 0)` there terminates the process.
  - It is a whole cross-platform mechanism to avoid a two-syscall window that the factory already accepts.
- **`fcntl F_GETLK` or `/proc/locks`, to test the lock without taking it.** Neither is portable. On Linux, `F_GETLK` doesn't even see flock locks.
- **Reading the train state file (`sdlc-factory-train.json`).** It shows a train is under way, not that a loop is running it. A train worked step by step through `/sdlc-factory:land` has one too.
- **The reader in `factory_records.py`.** That module is pure and parses only change-folder files. Trying a lock in the git common dir would break both.
- **The copy and the probe in `sdlc.py`, beside `SLOT_NAME`.** `status` doesn't need it. And a board already running would fail on every poll until restarted, because it reloads `board.py` but not `sdlc.py`.
- **A top-level `unattended` in `state.json`.** The page wouldn't redraw when it changed (see *Design*).
- **Flagging a train card "loop died" when the lock is free.** The board can't tell a dead loop from steps run by hand, and the intent asks only that the board never claim a live loop it can't see.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_board.py tests/test_modules.py tests/test_skills.py
uv run --group dev pytest -q -m portable tests/test_board.py
./check.sh
```

All three are healthy when every test passes, including the new R1–R13 tests. `check.sh` should end with ruff clean, formatting clean, the whole suite green and `claude plugin validate --strict` passing.

By hand, with two clones A and B:

1. In A, run `uv run --script scripts/sdlc.py board --port 5170`. It prints `"serving": true`.
2. In B, run the same command. It prints `{"refusals": ["port 5170 holds another repo's board: pass --port <N>"]}` and exits 1.
3. In a worktree of A, run it again. It prints `"serving": "already"`.

While a `factory.py train --run` is running in A, the train's cards show `running unattended`. After the loop exits, the line goes on the next poll, and `ls "$(git rev-parse --git-common-dir)"` shows no lock file that wasn't there before the board ran.

