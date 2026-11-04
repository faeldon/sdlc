---
id: 041
slug: windows-lock
kind: spec
created: 2026-11-04
updated: 2026-11-04
---

# 041 — Run the script on Windows · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. No script the plugin runs (`scripts/sdlc.py`, `scripts/metrics.py`, `scripts/trackers/*.py`,
   `plugins/factory/scripts/factory.py`) imports a module that exists on only one platform at module
   level. A test loads `sdlc.py` with `fcntl` unavailable (`sys.modules["fcntl"] = None`) and fails
   if the load raises.
2. `_main_lock()` locks a file, not a directory: `sdlc.lock` in the main checkout's git common dir
   (`git rev-parse --git-common-dir`), or `.sdlc/lock` outside git. It takes `fcntl.flock` on POSIX
   and `msvcrt.locking` on Windows, waits until it gets the lock, and releases it when the `with`
   block exits, an exception included.
3. The lock still excludes: `test_concurrent_claims_get_distinct_numbers`,
   `test_concurrent_worktree_claims_get_distinct_numbers` and
   `test_inbox_commit_waits_for_the_lock_claim_takes` pass unchanged, on macOS and in the Windows CI
   job.
4. The lock file never shows in `git status` in the main checkout or any worktree. A test takes the
   lock in a scratch repo and asserts `git status --porcelain` is empty.
5. Every script writes UTF-8 to stdout and stderr whatever the console's code page:
   `sdlc.py`'s and `factory.py`'s `main()` reconfigure both streams first. A test runs
   `sdlc.py status` through `uv run --script` with `PYTHONIOENCODING=cp1252` and asserts exit 0
   and a `■` in its output.
6. Every `subprocess.run` that reads text decodes it as UTF-8, not with the locale's code page:
   strictly for git and `gh`, whose output the plugin parses, and with `errors="replace"` for a
   host's own commands, whose output is only shown or recorded. A test walks each script's AST
   and fails on a `subprocess.run` with `text=True` and no `encoding=`.
7. A host's commands (`after_bump`, `prepare`, `publish`, `retro.evidence`, a project field's
   lookup, the `command` tracker) and an acceptance check's `sh` block all run through one
   helper, `sh -c <command>`: `/bin/sh` on POSIX, as `shell=True` uses today, and on Windows the
   `sh` that `shutil.which` finds (Git for Windows', which Claude Code needs there). With no `sh`
   on Windows, the command is refused with a message naming Git for Windows, not run under `cmd.exe`.
   `trackers/command.py` keeps its own copy of the helper, pinned to `sdlc.py`'s by a test.
8. Every file the scripts write has LF line endings on every platform (`newline="\n"`), so a
   Windows host without `core.autocrlf` commits no CRLF the plugin made. A test pins that each
   `write_text`/`open(..., "w")` in the scripts passes `newline=`.
9. Paths the scripts compare with git's output or show as repo paths are POSIX (`as_posix()`):
   `_shown()`, readiness's `./scripts/…sh` candidates, and uninstall's `left` list, which on
   Windows would otherwise list every tracked file again and miss the `own` prefix.
10. A GitHub Actions workflow, `.github/workflows/check.yml`, runs on every push and by hand
    (`workflow_dispatch`): on `ubuntu-latest`, ruff, the format check and the whole suite; on
    `windows-latest`, the tests marked `portable` (a marker registered in `pyproject.toml`). These
    are the import guard, the lock tests, the UTF-8 tests, the shell helper's tests and
    `tests/test_adoption.py`, which runs a change from `new` to `close` through `uv run --script`.
11. `.github/workflows/` joins `[review] sensitive` in `.sdlc/config.toml`, so a change to CI gets
    the deep review.
12. README says which platforms run the plugin (macOS, Linux, and Windows with Git for Windows),
    and `docs/REFERENCE.md` says host commands run as `sh -c` on every platform. AGENTS.md gains
    the rules a later change must keep: no single-platform import, UTF-8 subprocess decoding, LF
    writes, host commands through the helper, and a test that must pass on Windows marked
    `portable`.

## Design

**The lock.** `_main_lock(home)` resolves its file with one `_git(home, "rev-parse",
"--path-format=absolute", "--git-common-dir")`, the call `main_root()` already makes, falling back
to `main_root(home) / ".sdlc" / "lock"` outside git (the tests' bare `tmp_path`). It opens the file
`os.O_RDWR | os.O_CREAT` and calls a pair chosen once at import by `os.name`:

- POSIX: `fcntl.flock(fd, LOCK_EX)` / closing the fd releases it, as today.
- Windows: seek to 0, then `msvcrt.locking(fd, LK_NBLCK, 1)` in a loop with a 50 ms sleep on
  `OSError` (`LK_LOCK` gives up after ten tries, so it can't be the blocking wait), and
  `LK_UNLCK` before closing. Locking byte 0 of an empty file is allowed on Windows.

`fcntl` and `msvcrt` are imported inside that platform branch, never at module level. The lock
file stays after release: removing it would let a waiter hold a lock on a name a new caller
recreates (the unlink race). It is zero bytes, in `.git/`, which no tree or `git status` shows,
and shared by every worktree because the common dir is.

**Encoding.** Each script's `main()` starts with `sys.stdout.reconfigure(encoding="utf-8")` and the
same for stderr. `_git()` and the other parsed calls pass `encoding="utf-8"`; the trackers' `gh`
calls the same. The host-command helper passes `encoding="utf-8", errors="replace"`.

**One shell.** `_sh_argv(command) -> list[str] | str`: `["/bin/sh", "-c", command]` on POSIX, and
on Windows `[shutil.which("sh"), "-c", command]`, or a refusal string when `which` finds none. Each
of the seven call sites, `cmd_accept`'s `["sh", "-c", …]` included, calls it and reports the
refusal through its existing error path (a failed `after_bump`, a failed check). Running through
`sh` on Windows too means a host's commands mean the same thing in every session, and match the
Git Bash the skills' own blocks run in.

**Line endings.** The 12 `write_text` calls and `_write_state()` pass `newline="\n"`. Reads already
normalise through universal newlines, so hashes in `.sdlc/setup.json` don't move.

**Paths.** `_shown()`, the readiness candidates and uninstall's `left` use `as_posix()`. Git
accepts forward slashes on Windows, so nothing that passes a path to git changes.

**CI.** One workflow, two jobs, both with `astral-sh/setup-uv` and `uv run --group dev`. `claude
plugin validate` stays in `./check.sh` only: the CLI isn't on a runner. Since only `/sdlc:publish`
pushes, CI runs when a release is published, or by hand before it.

## Contracts touched

- **Never a number twice** (AGENTS.md, *Numbering*): `claim()` still takes its number under one
  exclusive lock that every worktree shares. One edge: a session running a pre-041 copy (locking
  the directory) and one running 041's (locking the file) don't exclude each other. It lasts only
  while two copies of the plugin run against one repo at once, and closes once both update.
- **The main checkout is never dirty** (AGENTS.md, *Numbering*; `inbox-commit`, `retro-commit`
  and `_release_refusals()` refuse a dirty one): the lock file is in the git dir, never the tree (R4).
- **Script dependencies inline**: none added. `msvcrt` and `fcntl` are the standard library.
- **Trackers never import `sdlc.py`**: so `command.py` gets its own copy of the shell helper,
  pinned by a test, as `factory.py`'s copies of `risk_paths()` already are.
- **Only publish pushes**: the workflow pushes nothing. It runs on pushes, which only publish
  makes.
- **Narrow `allowed-tools`**: no skill changes.
- **Nothing about a project or a workspace**: the workflow and tests use neutral names.

## Alternatives rejected

- **`msvcrt.locking` on the directory.** Windows won't `os.open` a directory, which is half the bug.
- **A lock file in `.sdlc/` behind an ignore rule.** It means a gitignore line every host's setup
  has to write and `uninstall` remove, and a host that misses it gets a dirty main checkout that
  `inbox-commit` and `retro-commit` refuse. The git dir needs neither.
- **The `filelock` package.** A new dependency in the PEP 723 block, for about twenty lines the
  standard library does.
- **`mkdir` as the lock.** A crash leaves it held for good, which `flock` and `msvcrt` never do,
  since the OS releases a dead process's lock.
- **`cmd.exe` for host commands on Windows (`shell=True` as is).** A host's `./check.sh`-style
  commands, written for the skills' Git Bash, would fail there only, and the same config would
  mean two things.
- **Re-executing under `python -X utf8`.** `os.execv` on Windows spawns a new process and returns
  control oddly to the caller. Reconfiguring the streams and naming the encoding per call is
  explicit.
- **The whole suite on Windows now.** Its fakes are shebang scripts (`FAKE_GH`, the hooks) that
  Windows can't exec. Porting them is its own change, so the Windows job runs what's marked
  `portable`, the adoption test among it.

## Verification

```bash
./check.sh                                               # the gate, on macOS
uv run --group dev pytest -q -m portable                 # what the Windows job runs, here first
PYTHONIOENCODING=cp1252 uv run --quiet --script scripts/sdlc.py status   # exits 0, prints ■
```

Healthy: the gate is green with the new tests counted, the `portable` subset passes on its own, and
`status` under cp1252 exits 0. Then, from the change's branch, `gh workflow run check.yml --ref
041-windows-lock` once the branch reaches the remote (by hand, since nothing here pushes): both jobs
green is the only proof this change has from Windows itself, and ship says whether it ran.
