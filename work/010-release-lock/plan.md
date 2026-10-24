---
id: 010
slug: release-lock
kind: plan
created: 2026-10-24
updated: 2026-10-24
---

# 010 — A release leaves the host's lock file in step with its version · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it.

## Context

`sdlc.py release` bumps `release.version_files` but not a lock file generated from them, and a lock
can't be a version file (`uv.lock` has a `version =` line per package). This repo's `uv.lock` has
been stuck at 1.0.0 since `d361c6c`, so every `uv run` dirties the tree. The spec
(`work/010-release-lock/spec.md`, R1–R9) adds `release.after_bump`: a host command release runs
after the bump, whose tracked changes go into the `Release X.Y.Z` commit. This plan is saved as
`work/010-release-lock/plan.md` once approved.

## Files to change

- `scripts/sdlc.py`:
  - `CONFIG_KEYS["release"]` gets `after_bump`.
  - A new constant `AFTER_BUMP_TIMEOUT = 600`, beside `EVIDENCE_TIMEOUT`.
  - `cmd_release` gets the new step, the changed-file detection and a shared `restore()`.
- `tests/test_release.py`: new tests for R1–R4 and R6; the existing ones stay unchanged (R5).
- `tests/test_skills.py`: `READS_CONFIG["sdlc:release"]` gets `release.after_bump` (R7).
- `skills/release/SKILL.md`: Step 0 names the key, Step 1 shows the command, and the WAIT names it
  when set (R7).
- `docs/REFERENCE.md`: an `after_bump` line in the `[release]` example, and a clause in the release
  prose (~line 347) (R8).
- `defaults/SDLC.md` and `.sdlc/SDLC.md`: the same clause in the release step (~line 310 / 330) (R8).
- `.sdlc/config.toml`: `after_bump = "uv lock"` under `[release]` (R9).
- `uv.lock`: committed at 1.1.0, as `uv lock` writes it (R9).
- `.sdlc/setup.json`: re-recorded with `uv run --quiet --script scripts/sdlc.py record` (R9).

## Work order

1. **Config key.** Add `"after_bump": None` to `CONFIG_KEYS["release"]`, commented like `publish`
   ("run by /sdlc:release after the bump; what it changes is committed too; {version}, {tag}").
   `load_config()` is generic over `CONFIG_KEYS`, so it needs nothing else. Add
   `AFTER_BUMP_TIMEOUT`.
2. **`cmd_release`.**
   - When building the plan, next to `tag` and `notes` (only when the key is set): put the command,
     formatted the way `cmd_publish` does it (`rel["after_bump"].format(version=shlex.quote(new),
     tag=shlex.quote(tag))`), in `report["after_bump"]`, and set `report["untracked"] = []`. With
     the key unset, neither key appears (R5).
   - `restore()`: the `git reset -q HEAD -- *files` and `git checkout -q -- *files` pair moved out of
     `commit()`, so `commit()` and the new step share it.
   - `run_after_bump()`:
     - Take `before = _untracked(home)`.
     - Run `subprocess.run(command, shell=True, cwd=home, capture_output=True, text=True,
       errors="replace", timeout=AFTER_BUMP_TIMEOUT)`, with `TimeoutExpired` and `OSError` caught.
     - Read `changed` from `git diff --name-only -z` (modified and deleted tracked files). Append
       each path not already in `report["files"]`. Put `_untracked(home) - before` in
       `report["untracked"]`, sorted.
     - On failure (non-zero exit, timeout or OSError), call `restore()` (it covers the appended
       files too) and return `release.after_bump exited N: <stderr[:500]>`, or the timeout or
       OSError text.
   - `_untracked(home)` is a small helper: the set from `git ls-files --others --exclude-standard
     -z`.
   - The steps list gets `("after bump", run_after_bump)` after `changelog`, only when it's set.
     `--check` then lists `after bump (--check)` with the others (R6).
   - Run `uv run --group dev pytest tests/test_release.py -q`: the existing tests still pass (R5).
3. **Tests**, in `tests/test_release.py`, using `_repo` with `CONFIG + 'after_bump = "..."\n'` and a
   tracked `uv.lock` committed in the repo:
   - `test_after_bump_runs_with_the_version_and_its_changes_are_committed` (R1, R2): `after_bump =
     "echo {version} >> uv.lock"`. `done` is `["version files", "after bump", "commit", "tag"]`,
     `uv.lock` ends with `0.4.3`, the release commit's files are `pkg.json`, `pyproject.toml` and
     `uv.lock`, and `git status --porcelain` is empty.
   - `test_files_after_bump_creates_are_reported_not_committed` (R3): `"touch made.txt"`. `made.txt`
     is in `untracked`, not in the commit, and still on disk.
   - `test_a_failed_after_bump_puts_everything_back` (R4): `"echo x >> uv.lock; exit 1"`. Exit 1,
     `release.after_bump exited 1` in `refusals`, skipped is `["after bump", "commit", "tag"]`, HEAD
     unchanged, no `v0.4.3` tag, and `git status --porcelain --untracked-files=no` empty.
   - `test_check_shows_after_bump_and_runs_nothing` (R6): `"touch ran"`. With `--check`, `after_bump
     == "touch ran"`, `after bump (--check)` is in skipped, and `ran` doesn't exist.
   - `test_after_bump_stays_out_of_the_report_when_unset` (R5): the plain repo's output has neither
     `after_bump` nor `untracked`.
4. **Skill and the test that reads it** (R7):
   - Add `release.after_bump` to `READS_CONFIG["sdlc:release"]`.
   - Step 0 says `release.after_bump` is the command run after the bump, if any.
   - Step 1 shows `after_bump` and says its tracked changes are committed with the release and
     anything new it leaves untracked is listed, not committed.
   - The WAIT gains `, run <after_bump> and commit what it changes` when set, said as for the
     changelog.
   - Step 3 says a failure there puts the files back like a failed commit.
   - Run `uv run --group dev pytest tests/test_skills.py -q`.
5. **Docs** (R8):
   - REFERENCE's `[release]` example gets `after_bump = "uv lock"  # optional: run by /sdlc:release
     after the bump; what it changes is committed with it; {version}, {tag}`.
   - Its prose gets "runs `release.after_bump` if set (a lock file regenerated from the new
     version), and commits what that changes too".
   - The same clause goes in `defaults/SDLC.md` and `.sdlc/SDLC.md`, keeping line wrap at 100.
6. **This repo** (R9):
   - Add `after_bump = "uv lock"` to `.sdlc/config.toml` `[release]`, with a one-line comment.
   - Run `uv lock` so `uv.lock` reads 1.1.0.
   - Run `uv run --quiet --script scripts/sdlc.py record` from the worktree.
   - Run `./check.sh`, then `git status --short`: `uv.lock` stays as committed after the gate.

## Tests

- **R1 and R2:** `test_after_bump_runs_with_the_version_and_its_changes_are_committed`.
- **R3:** `test_files_after_bump_creates_are_reported_not_committed`.
- **R4:** `test_a_failed_after_bump_puts_everything_back`.
- **R5:** every existing `tests/test_release.py` test, unchanged, plus
  `test_after_bump_stays_out_of_the_report_when_unset`.
- **R6:** `test_check_shows_after_bump_and_runs_nothing`.
- **R7:** `test_skills_read_host_specifics_from_config`, with the new `READS_CONFIG` entry, plus the
  existing WAIT and rules tests in `tests/test_skills.py`.
- **R8:** manual, by reading the diff. No test checks REFERENCE's keys.
- **R9:**
  - 008's `test_this_repos_setup_record_is_current` (the new key and the defaults edit both need
    `record`).
  - Manual: after `./check.sh`, `git status --short` shows no `uv.lock` change.
- **The timeout branch:** reviewed in the code. A test would wait out the 600s, so it isn't
  monkeypatched.

## Rollback

`git revert <sha>` of the change's commit removes the key, the step, the docs and the lock refresh.

What a revert doesn't cover:
- **A host that already set `after_bump`:** after the revert, its config holds a key the plugin
  doesn't read. It gets an `unknown` warning from `config` and `drift` and must delete the line;
  nothing else breaks.
- **A release already cut with it:** its commit keeps the lock change, which is the point.
