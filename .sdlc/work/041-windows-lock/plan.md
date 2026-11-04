---
id: 041
slug: windows-lock
kind: plan
created: 2026-11-04
updated: 2026-11-04
---

# 041 — Run the script on Windows · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: the lock (R1–R2), `_utf8_streams()` at `main()` (R5), `encoding=` on every
  text `subprocess.run` (R6), `_sh_argv()` and its seven call sites (R7), `newline="\n"` on its
  12 `write_text` calls (R8), `as_posix()` in `_shown()` (line 748), readiness's `.sh` candidates
  (~6314) and uninstall's `left` (~7086) (R9).
- `scripts/trackers/command.py`: its own `_sh_argv()` copy plus UTF-8 with replace (R6, R7).
- `scripts/trackers/github.py`: `encoding="utf-8"` on its three `subprocess.run` calls (R6).
- `plugins/factory/scripts/factory.py`: `_utf8_streams()` at `main()`, `encoding=` on `_git`
  (line 112), `newline="\n"` on its 6 writes (R5, R6, R8).
- `pyproject.toml`: register the `portable` marker under `[tool.pytest.ini_options]` (R10).
- `.github/workflows/check.yml` (new): ubuntu runs the full suite, windows runs `-m portable` (R10).
- `.sdlc/config.toml`: add `".github/workflows/"` to `[review] sensitive` (R11).
- `tests/test_windows.py` (new, `pytestmark = pytest.mark.portable`): the new tests below.
- `tests/test_sdlc.py`, `tests/test_bugs.py`: mark the three lock tests `portable` (R3).
- `tests/test_adoption.py`, `tests/test_acceptance.py`: module-level `portable` marker. Skip one
  test on `win32` only if it needs what Windows lacks (e.g. the `symlink_to` at line 361), with
  the reason in the skip.
- `README.md`: a platforms line (R12).
- `docs/REFERENCE.md`: host commands run as `sh -c` everywhere, Git for Windows' `sh` there (R12).
- `AGENTS.md`: the portability rules, under the invariants the tests enforce (R12).

## Work order

1. **Lock (R1–R4).**
   - Replace `import fcntl` with a branch on `os.name` that defines `_lock(fd)`/`_unlock(fd)`:
     POSIX uses `fcntl.flock`; Windows uses `msvcrt.locking(fd, LK_NBLCK, 1)` after
     `os.lseek(fd, 0, 0)`, retried with a `time.sleep(0.05)`, and `LK_UNLCK` on release.
   - Add `_lock_path(home)`: `<git-common-dir>/sdlc.lock` via `_git(home, "rev-parse",
     "--path-format=absolute", "--git-common-dir")`, the call `main_root()` makes, else
     `main_root(home)/.sdlc/lock`.
   - `_main_lock()` opens it `O_RDWR | O_CREAT` and releases it in `finally`. Update its
     docstring and `claim()`'s ("an exclusive lock on the main checkout's `.sdlc/`").
   - Tests: the import guard loads the script by path with `sys.modules["fcntl"] = None`,
     `os.name` patched to `"nt"` and a fake `msvcrt` in `sys.modules` (`locking` backed by a
     `threading.Lock` per path, raising `OSError` when held), then claims two numbers from two
     threads and gets distinct ones. That proves no module-level `fcntl` and exercises the
     Windows branch's retry loop on macOS. The real `msvcrt` runs in CI.
   - Test: `git status --porcelain` is empty after `_main_lock` in a scratch repo, and the lock
     file is in the git dir.
   - Run the three existing lock tests unchanged.
2. **UTF-8 (R5, R6).**
   - `_utf8_streams()`: for `sys.stdout` and `sys.stderr`, `reconfigure(encoding="utf-8")` when
     the stream has it, inside `try` (pytest's capture streams must not break). Call it first in
     `sdlc.py`'s and `factory.py`'s `main()`.
   - Add `encoding="utf-8"` beside every `text=True` on git and `gh` calls. That's about 17 in
     `sdlc.py` (`_git` at 615, 1745, 2485, 3015, 3058, 3405, 4123, 5589, 5845, …), three in
     `github.py`, and one in `factory.py`.
   - Host commands get `encoding="utf-8", errors="replace"`. `cmd_accept`'s timeout `text()`
     helper already decodes with replace.
   - Tests: run `sdlc.py status` through `uv run --script` with `PYTHONIOENCODING=cp1252` in a
     scratch repo: exit 0, `■` in stdout decoded as UTF-8. Add an AST walk over the four scripts'
     files that fails on any `subprocess.run` call with `text=True` and no `encoding` keyword.
3. **One shell (R7).**
   - `_sh_argv(command) -> tuple[list[str] | None, str | None]` returns `(["/bin/sh", "-c",
     command], None)` on POSIX. On Windows, `which = shutil.which("sh")` gives
     `([which, "-c", command], None)`, or `(None, "no sh found: install Git for Windows, whose sh
     the plugin runs host commands with")`.
   - Replace `shell=True` at 2019 (lookup), 4278 (after_bump), 4309 (prepare), 4446 (publish
     command) and 4807 (evidence), and `["sh", "-c", …]` at 2210 (accept). Each refusal goes out
     through that site's existing error path: the lookup's `row["error"]`, the release step's
     return string, accept's failed result with the message as `output`, evidence's `error`.
   - Copy the helper into `trackers/command.py` for its line 45.
   - Tests: on POSIX `_sh_argv` gives `/bin/sh`. With `os.name` patched to `"nt"` and
     `shutil.which` patched to return None, it gives the refusal, and a release whose
     `after_bump` hits it reports the refusal. The AST of `command.py`'s copy must equal
     `sdlc.py`'s (the pattern of factory's pinned `risk_paths()` test in `tests/test_factory.py`).
4. **LF writes (R8).** Add `newline="\n"` to the 12 `write_text` calls in `sdlc.py`, which
   include `_write_state`'s `tmp.write_text` (3714), and to the 6 in `factory.py`. Test: an AST
   walk fails on a `write_text` or a write-mode `open` without `newline=` in any of the four
   scripts.
5. **POSIX paths (R9).**
   - `_shown()` returns `path.relative_to(root).as_posix()`.
   - Readiness uses `rel.as_posix()` in both the command and its source.
   - Uninstall builds `left` from `p.relative_to(home).as_posix()`.
   - Tests: readiness's candidate under `scripts/` reads `./scripts/ci.sh`. That already passes
     on POSIX, so mark it `portable` (tests/test_readiness.py:95) so Windows proves it. Same for
     an uninstall `left` test if one exists, else add one in `test_windows.py`.
6. **Markers and CI (R10, R11).**
   - In `pyproject.toml`: `markers = ["portable: must pass on Windows too; the Windows CI job
     runs only these"]`.
   - In `check.yml`: `on: [push, workflow_dispatch]`, with `actions/checkout@v4` and
     `astral-sh/setup-uv@v6` in two jobs:
     - `linux` runs `uv run --group dev ruff check .`, `ruff format --check .` and `pytest -q`;
     - `windows` (`windows-latest`, `shell: bash`) runs `uv run --group dev pytest -q -m portable`.
     No `claude plugin validate`, since the CLI isn't on a runner.
   - Add the sensitive path to `.sdlc/config.toml`.
7. **Docs (R12).**
   - README: macOS, Linux, and Windows with Git for Windows (Claude Code needs it there too).
   - REFERENCE, where `after_bump`/`prepare`/`publish`/`retro.evidence`/lookup commands are
     described: they run as `sh -c`.
   - AGENTS.md: one bullet under *Invariants the tests enforce* naming `tests/test_windows.py`:
     no single-platform import at module level, `encoding=` on text subprocess calls,
     `newline="\n"` on writes, host commands through `_sh_argv()`, and `portable` on a test that
     must pass on Windows.
8. **Gate and Windows proof.**
   - Run `./check.sh`, `uv run --group dev pytest -q -m portable`, and the cp1252 `status` run.
   - Then you push the branch yourself (nothing here pushes) and run `gh workflow run check.yml
     --ref 041-windows-lock`. Fix what the Windows job finds in this change. Ship reports whether
     it ran green.

## Tests

- R1: the import guard in `test_windows.py` (fake `msvcrt`, `fcntl` blocked, `os.name` `nt`).
- R2: the fake `msvcrt` exercises the Windows branch's retry. The lock file is in the git dir, or
  `.sdlc/lock` outside git.
- R3: the three existing lock tests, now `portable`.
- R4: `git status --porcelain` is empty after taking the lock.
- R5: `status` under `PYTHONIOENCODING=cp1252` through `uv run --script`.
- R6: the AST walk for `encoding=`.
- R7: `_sh_argv` on POSIX, the refusal on a patched Windows with no `sh`, the copy pinned to
  `command.py`, and `test_acceptance.py` marked portable, so accept's `sh` runs on Windows.
- R8: the AST walk for `newline=`.
- R9: the readiness candidate test and an uninstall `left` test, both `portable`.
- R10: the workflow running green on both jobs. That's manual: you push and dispatch, and ship
  says whether it ran.
- R11: `risk_paths()` names `.github/workflows/check.yml` as sensitive. One assert in
  `test_risk.py` against this repo's config.
- R12: the docs, read in ship's context pass.

## Rollback

`git revert <sha>` undoes all of it. Two things the revert doesn't cover:
- `sdlc.lock` is a zero-byte file the new lock leaves in each repo's git dir. Remove it with
  `rm "$(git rev-parse --git-common-dir)/sdlc.lock"`, though a leftover is harmless.
- The workflow's runs on GitHub stay in its Actions history. A revert stops new runs.

Files a host gets at setup don't change, so `/sdlc:setup` doesn't need rerunning.
