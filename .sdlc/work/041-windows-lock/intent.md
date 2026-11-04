---
id: 041
slug: windows-lock
tier: 2
impact: minor
stage: shipped
created: 2026-11-04
updated: 2026-11-04
shipped: 2026-11-04
idea:
depends_on:
fixes: [2026-11-04-11]
serves: [O1]
---

# 041 — Run the script on Windows

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`scripts/sdlc.py` can't start on native Windows. It imports `fcntl` at module level
(`scripts/sdlc.py:90`), a module that exists only on Unix, so every command dies with
`ModuleNotFoundError: No module named 'fcntl'` before it does anything, and every skill with it at
its Step 0, setup's `readiness`, `config` and `drift` included. A host on Windows reported exactly
that: uv 0.13.7 installed, then `/sdlc:setup` failed on the script's second line, writing nothing.

The import has one use, `_main_lock()` (`scripts/sdlc.py:1780`): the exclusive lock `claim()`
hands out a local number under and `inbox-commit` writes the register under from a worktree. It
`flock`s a descriptor opened read-only on the main checkout's `.sdlc/` directory, which Windows
won't open at all, so `msvcrt.locking` in place of `flock` would still fail on the `os.open`: the
lock needs a file.

Nothing caught it: `./check.sh` and `tests/test_adoption.py` run only where the author works, on
macOS. The import has been there since 1.0.0.

## Outcome

- `sdlc.py` imports and runs on native Windows: no module-level `fcntl`, and `_main_lock()` takes
  a lock that works there (`msvcrt.locking`) and on Unix (`flock`), on a file, not a directory.
- The lock still excludes: two `claim()`s from two worktrees never get one number, on either
  platform, as today's test pins for Unix.
- The lock file never shows in `git status`, so `inbox-commit`, `retro-commit` and `release`, which
  refuse a dirty main checkout, are never refused over it.
- A test fails if the script stops loading with `fcntl` unavailable (`sys.modules["fcntl"] =
  None`), or stops claiming a number that way, so a Unix-only import can't come back unnoticed.
- **Moves O1:** a host on Windows gets from `/sdlc:setup` to its first closed change, and no issue
  filed against setup, `new` or close names the platform.

## Affected

- **Area:** the script's import block and its one lock.
- **Files & components:** `scripts/sdlc.py` (`_main_lock()`, with `claim()` and
  `cmd_inbox_commit()` above it); `scripts/metrics.py`, `scripts/trackers/*.py` and the factory's
  `factory.py`, loaded the same way and worth checking for Unix-only imports; `tests/` for the
  lock's tests and a new import guard.
- **Downstream:** every host on Windows, where nothing runs today, and every host on Unix, whose
  numbering and inbox commits go through this lock.
- **Contracts:** numbering (never two schemes, never a number twice); the inline PEP 723
  dependencies mirrored in `pyproject.toml`'s `dev` group.

## Constraints

- **Never a number twice.** The lock keeps excluding across every worktree of one repo, scoped to
  the main checkout as `main_root()` finds it.
- **The main checkout stays clean.** A lock file in the tree would be untracked and make
  `inbox-commit` and `retro-commit` refuse, so it lives outside the working tree (under the git
  common dir, say) or is ignored by a rule setup needn't write.
- **Dependencies stay inline.** No new package unless it goes in the PEP 723 block and the `dev`
  group together; the standard library (`msvcrt`, `fcntl`) is preferred.
- **Unix behaves as now:** a blocking exclusive lock, released when the `with` block exits, a crash
  included.

## Open questions

- ~~Where the lock file lives: under `git rev-parse --git-common-dir` (never in the tree, shared by
  every worktree), or in `.sdlc/` behind an ignore rule.~~ Resolved: `sdlc.lock` in the git common
  dir, `.sdlc/lock` outside git (spec R2).
- ~~Whether to stop at the lock or also sweep for the next Windows failures: host commands run with
  `shell=True` (`cmd.exe` there, so `./check.sh` won't run as a gate), and paths handed to git may
  need forward slashes. Without a Windows machine or CI, what's proven beyond the import guard?~~
  Resolved: the full sweep, UTF-8 streams and decoding, one `sh -c` helper, LF writes and POSIX
  paths (spec R5–R9).
- ~~Whether to add a Windows CI job, which this repo has none of, or state platform support in the
  README, and how strongly.~~ Resolved: both, a `windows-latest` job over the `portable` tests and
  a README line (spec R10, R12).
- ~~Whether `msvcrt.locking` (a byte-range lock that must be retried for a blocking wait) or a
  lock file with retry is simpler to get right.~~ Resolved: `msvcrt.locking` with `LK_NBLCK`
  retried every 50 ms (spec Design).
