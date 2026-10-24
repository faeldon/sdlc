---
id: 010
slug: release-lock
kind: spec
created: 2026-10-24
updated: 2026-10-24
---

# 010 — A release leaves the host's lock file in step with its version · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `release.after_bump` is a new config key in `CONFIG_KEYS["release"]`, `None` by
   default. When set, `sdlc.py release` runs it after the version files and the changelog are
   written and before the commit, through the shell, from the main checkout. `{version}` and
   `{tag}` are replaced, shell-quoted, as `release.publish` does it. A test asserts the command ran
   with the new version substituted.
2. **R2.** Every tracked file the command changed (modified or deleted) goes into the
   `Release X.Y.Z` commit, alongside the version files and the changelog. A test that runs `echo`
   into a tracked `uv.lock` asserts the release commit contains the change and the tree is clean
   afterwards.
3. **R3.** New untracked files that appear while the command runs are listed in the report as
   `untracked` and never committed. A test asserts such a file is listed, absent from the commit
   and still on disk.
4. **R4.** If the command exits non-zero, times out (`AFTER_BUMP_TIMEOUT`, 600s) or can't start,
   release stops before the commit. Its report names the step and the command's error output. It
   puts back every tracked file the release or the command changed, so a rerun finds `main` as it
   was. A test with a command that edits `uv.lock` and then exits 1 asserts there's no new commit,
   no tag, and no tracked file changed.
5. **R5.** With no `after_bump` set, release behaves exactly as now: the same steps, files and
   output keys. The existing `tests/test_release.py` passes unchanged.
6. **R6.** `release --check` runs nothing. It shows the formatted command as `after_bump` and lists
   `after bump (--check)` among the skipped steps. A test whose command would create a marker file
   asserts the file doesn't exist afterwards.
7. **R7.** `/sdlc:release` names the command in its plan and in its WAIT question when one is set.
   `release.after_bump` joins `READS_CONFIG["sdlc:release"]`, so
   `test_skills_read_host_specifics_from_config` enforces it.
8. **R8.** `docs/REFERENCE.md` lists the key in the `[release]` example with what it does.
   `defaults/SDLC.md`'s release step mentions it, with the same edit in `.sdlc/SDLC.md`.
9. **R9.** This repo sets `after_bump = "uv lock"` and commits `uv.lock` at 1.1.0.
   `.sdlc/setup.json` is re-recorded, so 008's drift gate passes with the new key and the default
   edit.

## Design

- **The new step.** `cmd_release` gets a step `("after bump", run_after_bump)` between `changelog`
  and `commit`, present only when `rel["after_bump"]` is set. The command is formatted while the
  plan is built (after the refusals, next to `tag` and `notes`), so `--check` shows it.
- **Running it.** The step follows `run_command()` in `cmd_publish`:
  `subprocess.run(shell=True, cwd=home, capture_output=True, text=True,
  timeout=AFTER_BUMP_TIMEOUT)`. A non-zero exit, a timeout or an `OSError` becomes an error string
  carrying stderr (capped, like `_evidence`'s 500 characters).
- **Finding what it changed.** `_release_refusals` already refuses a main checkout with uncommitted
  tracked changes, so before the step the only tracked changes are the version files and the
  changelog. After it, `git diff --name-only` (modified and deleted) minus `report["files"]` is what
  the command changed, and those paths are appended to `report["files"]`. That list is already
  what `commit()` adds and what its rollback restores. New untracked files are found by comparing
  `git ls-files --others --exclude-standard` before and after, reported as `untracked`, and never
  added.
- **Rolling back.** One helper, `restore()`, does what `commit()` does on failure today:
  `git reset -q HEAD -- files` then `git checkout -q -- files`. The after-bump step and the commit
  step both call it when they fail. Untracked files the command made are left where they are, and
  the report lists them.
- **The skill.** `skills/release/SKILL.md` Step 0 names `release.after_bump`. Step 1 shows the
  command and says what it may change. The WAIT gains "`run <after_bump> and commit what it
  changes,`" when one is set. No new `allowed-tools`: the command runs inside `sdlc.py release`,
  which the skill already has a rule for.
- **This repo.** `.sdlc/config.toml` sets `after_bump = "uv lock"`. `uv.lock` is committed at
  1.1.0. `record` runs after the `defaults/SDLC.md` edit and the new key.

## Contracts touched

- **Only publish pushes** (`test_only_publish_pushes`): the new code never pushes, and the word
  `push` stays out of it. A host command that pushes on its own is outside what the plugin can
  enforce. The REFERENCE line says the command must leave the commit and the push to the plugin.
- **Mechanism vs. policy:** the plugin doesn't know a host uses uv. The host names the command, and
  the plugin only runs it and commits what changed.
- **Narrow `allowed-tools` / one WAIT:** unchanged. The command runs inside a command the skill is
  already allowed to run, and the WAIT, which shows it, is the one approval.
- **Every refusal before anything is written:** the up-front checks are unchanged. The command can
  only fail at run time, and R4 puts the tree back.
- **A config key added:** this is the "always Tier 2" rule. `RETIRED_KEYS` gets no entry, since
  nothing is renamed. Hosts already set up see it as `new` in `drift`, through `/sdlc:setup`.
- **This repo tracks the defaults:** the `defaults/SDLC.md` edit is made the same way in
  `.sdlc/SDLC.md`, and `record` runs (R9).

## Alternatives rejected

- **`uv.lock` in `version_files`:** `read_versions()` refuses a file with more than one `version`
  line, and loosening that would let release edit the wrong package's line.
- **A configured list of the files the command may change:** a second key that can disagree with
  the first. Comparing tracked files is exact, because release already starts from a clean tree.
- **The plugin running `uv lock` when it sees `uv.lock`:** that puts knowledge of the host's build
  tool into the plugin.
- **Running it from `/sdlc:publish`:** too late, since the tag already points at a commit with the
  stale lock.
- **Under `[commands]`:** every other release setting lives in `[release]`.
- **Refusing a release while the lock is stale:** the plugin can't tell what "stale" means for a
  host's tool, and running the command fixes it anyway.
- **`/sdlc:setup` suggesting the key when it finds a lock file:** possible later, but nothing asks
  for it yet.

## Verification

- `uv run --group dev pytest tests/test_release.py tests/test_skills.py -q`: the new R1–R7 tests
  pass, and the existing ones pass unchanged.
- `./check.sh`: passes in full, including 008's drift gate after `record`.
- `uv run --quiet --script scripts/sdlc.py release --check` from a scratch clone of this repo with
  a test tag: `after_bump` reads `'uv lock'` and the skipped steps include `after bump (--check)`.
- After this change, `uv run` leaves `uv.lock` unchanged: `git status --short` is empty after
  `./check.sh`.
