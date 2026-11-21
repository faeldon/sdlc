---
id: 206
slug: update-skill
kind: plan
created: 2026-11-21
updated: 2026-11-21
---

# 206 — A host learns of a new release and updates in one consistent run · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## What was recorded first (the spec's assumptions)

Recorded on Claude Code 2.1.311 before any code:

- `claude plugin list --json` exists, and prints a list of rows. Each row has `id`
  (`sdlc@sdlc`, `sdlc-factory@sdlc`), `version`, `scope` (`user`, `project`, `local`, plus scopes
  like `synced` that no update applies to), `enabled`, `installPath`, `installedAt`,
  `lastUpdated`, `projectEnabled`. A row at project or local scope also has `projectPath`. A row
  from a marketplace registered from a folder also has `readFromFolder`. An install from GitHub
  has no `readFromFolder`. The recorded rows, with neutral paths, are
  `tests/fixtures/plugin-list.json`.
- Claude Code keeps a row for **each worktree** a project-scope install was made in, its
  `projectPath` the worktree's own path. So "applies here" is `projectPath` equal to
  `main_root()`. A row whose `projectPath` is inside this repo's main checkout (a worktree's) is
  this repo's, not another repo's: it is neither a step nor `elsewhere` (D: default, below).
- The cached copy under `~/.claude/plugins/cache/sdlc/sdlc/1.11.0/` has no `.git` entry. The
  clone this repo's marketplace is read from does, so `in_place` holds here.
- Not checkable from a non-interactive build: that a SessionStart hook's `systemMessage` reaches
  the person, and that `--scope project` acts on the folder it runs in. Both are taken from Claude
  Code's hook and plugin docs. The spec's manual Verification step checks them.

## Files to change

- `scripts/sdlc.py`: the update logic, beside `setup_nudge()` and `plugin_version()`:
  `release_source()`, `in_place()`, `latest_release()`, `parse_installs()` (pure),
  `plugin_installs()`, `applies_here()`, `update_cache()`, `update_report()`, `update_line()`
  (pure), `update_nudge()`, `installed_check()`, `cmd_update()` and its `@command("update", …)`.
  `cli_status` sets `a["update"]`, and `print_status` prints it beside `■ Setup:`.
  `cmd_readiness` gains `uncommitted`. `HELP_ORDER` gains `update`. Reuses `_semver()`/`_older()`,
  `SEMVER_RE`, `_ledger_dir()`, `main_root()`, `read_manifest()`, `_dirty_paths()`, `_git()`.
- `hooks/hooks.json` (new): the one SessionStart hook.
- `skills/update/SKILL.md` (new): `/sdlc:update`.
- `skills/setup/SKILL.md`: Step 0 runs `update --installed` and stops on `restart first`; the
  `complete` stop and Step 6 name the commit from `uncommitted`.
- `scripts/retro.py`: `SKILL_RUNS` gains `sdlc:update: outside` (run from the main checkout).
- `tests/test_update.py` (new): R2–R9, R13, R14, R16's parts the code owns.
- `tests/fixtures/plugin-list.json` (new): the recorded output (R14).
- `tests/test_skills.py`: `GATED`, `READS_CONFIG` and `test_skills_were_found` gain the skill;
  `test_sdlc_loads_nothing_from_plugins` pins the one hook (R1); a test that setup names
  `update --installed`, `restart first` and `uncommitted` (R12).
- `tests/test_readiness.py`: `uncommitted` lists modified owned paths, none when clean (R12).
- `README.md` *Updating*, `docs/REFERENCE.md` *After an update*: the five steps (R15).
- `docs/FEATURES.md`, `docs/PROCESS.md`: the skill, its WAIT, the hook and `update` (R15).
- `AGENTS.md`: a paragraph on the hook and the cache (R10).

## Work order

1. **The pure parts.** `parse_installs()` from the recorded fixture, `applies_here()`, and
   `update_line()` for both R3 forms. Portable tests.
2. **The check and its cache.** `latest_release()` against a bare repo in `tmp_path`,
   `plugin_installs()` with `claude` resolved by `shutil.which`, `update_cache()` in the git
   common dir with the 24-hour rule and `latest: null` on failure. Tests record every argv.
3. **The command.** `cmd_update` with `--hook`, `--installed` and no flag; `in_place`; the steps
   in order; `elsewhere`. Tests for R2, R5, R8, R9.
4. **The hook** `hooks/hooks.json`, the changed pin, and the end-to-end test (R1, R13).
5. **Status** `update_nudge()` and its line (R7).
6. **Readiness and setup** `uncommitted`, setup's Step 0 and report (R12).
7. **The skill** `/sdlc:update` and the skill tests (R11).
8. **Docs** README, REFERENCE, FEATURES, PROCESS, AGENTS (R10, R15).

## Decisions taken as defaults

- An install from a folder (`readFromFolder`) is never stale and never a step: its version is
  whatever that folder holds, so a release says nothing about it. When the sdlc install that applies
  here at its most specific scope is one, the hook and `status` say nothing (the intent's "silent
  for a local-path marketplace").
- A row whose `projectPath` is a worktree of this repo is reported in `installs` as not applying,
  and listed neither in `steps` nor in `elsewhere`. Otherwise this repo's own list would name every
  worktree a change was ever built in.
- `steps` is empty unless an install is stale. A session that runs an old copy while every install
  is current gets `restart_first: true` and no steps; the skill says to restart.
- No `claude` (or an unreadable list) makes the hook and `status` silent even when `ls-remote`
  found a newer tag: without the installs the line can't be told right.
- Setup's `complete` stop can't hold the literal `git commit` (an existing test keeps every commit
  line in Step 6), so it points at Step 6's commit for the `uncommitted` paths.

## Where the build departed

- `tests/fixtures/close-output.json` is re-recorded at `1.11.0` (its `Sdlc-Runtime: plugin=`
  lines, nothing else). The `Release 1.11.0` commit moved the manifest and left the base branch
  red on `test_close_output_is_unchanged`. Round 1 pinned `plugin_version()` in the test instead;
  the person decided D1 for re-recording, so round 2 reverts that pin and the test is untouched.
- `setup_uncommitted()` sits above `cmd_readiness`, since `tests/test_registry.py` keeps each
  adapter right after its handler.
- `hooks/hooks.json` carries a `description` beside `hooks`, and a 30-second timeout. Each of
  `ls-remote` and `claude plugin list` gets `UPDATE_TIMEOUT` (10 s).
- `checks.md` holds R10's AGENTS.md paragraph and README's table row, which no test reads.

## Tests

- R1: `test_sdlc_loads_nothing_from_plugins` (changed): `hooks/` holds only `hooks.json`, one
  `SessionStart` hook, matcher `startup`, the literal command; no `hooks` key in the manifest.
  `claude plugin validate --strict` in the gate.
- R2: `test_hook_is_silent_when_it_can_t_tell` (no `claude` on PATH, `ls-remote` failing, outside
  a git repo: exit 0, no output).
- R3: `test_the_line_*` (both forms, joined stale installs), portable.
- R4: `test_one_check_a_day` (a second run the same day runs no `ls-remote` and no `claude`),
  `test_a_failed_check_is_cached_as_null`.
- R5: `test_in_place_is_never_told` (a `.git` in the fake plugin root: no line, no step, no
  network call).
- R6: `test_parse_installs_*` from the fixture, portable; `test_installs_failure_is_a_reason`.
- R7: `test_status_reads_the_cache_alone` (refuses any `claude` or `ls-remote` argv).
- R8: `test_steps_in_order` (two scopes, sdlc-factory, another repo's install), `test_current_has_no_steps`.
- R9: `test_installed_*` (newer project install over an older running copy is `true`; no `claude`
  is `null`).
- R10: the existing `READ_ONLY` test, unchanged; `test_update_is_not_read_only`.
- R11: `tests/test_skills.py`'s rule, gate and config tests over the new skill.
- R12: `test_readiness_lists_uncommitted_setup_paths`; `test_setup_names_the_restart_and_the_commit`.
- R13: `test_hook_end_to_end` (fake `claude`, bare repo, not portable).
- R14: `test_nothing_local` scans the fixture; it says which Claude Code version printed it.
- R15: `tests/test_feature_map.py` (skill and WAIT); `test_docs_list_the_five_steps`.
- R16: `tests/test_windows.py`, unchanged.

## Rollback

`git revert` takes out the hook, the skill and the command. It does not remove the
`sdlc-update.json` cache in each host's git common dir: harmless, read by nothing once reverted,
and `rm "$(git rev-parse --git-common-dir)/sdlc-update.json"` removes it. A `claude plugin update`
the skill ran is Claude Code's settings, undone by installing the older version
(`claude plugin install sdlc@sdlc --scope <scope>` at the version wanted).
