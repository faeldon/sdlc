---
id: 010
slug: release-lock
tier: 2
impact: minor
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea: Release bumps uv.lock with the version files
depends_on:
serves: none
---

# 010 — A release leaves the host's lock file in step with its version

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`sdlc.py release` (`cmd_release`, `scripts/sdlc.py:2848`) bumps the version line in each file
under `release.version_files`, commits `Release X.Y.Z` and tags it. A lock file generated from one
of those files doesn't get bumped with it. It can't be listed in `version_files` either:
`uv.lock` has one `version =` line per package, and `read_versions()` refuses any file with more
than one.

This repo hit it at 1.1.0. `d361c6c` bumped `pyproject.toml` to 1.1.0, but `uv.lock` still says
`version = "1.0.0"` for `sdlc`. Every `uv run` since, including the one inside `./check.sh`,
rewrites the lock, and each change has to revert that by hand: 008 did it twice and 009 three
times. Any host whose version file has a lock file generated from it is in the same position after
every release: `uv.lock` beside `pyproject.toml`, `package-lock.json` beside `package.json`,
`Cargo.lock` beside `Cargo.toml`.

## Outcome

- A host can name a command that release runs after the version bump, for example `uv lock`, and
  whatever it changes goes into the same `Release X.Y.Z` commit. The tree is clean right after a
  release.
- For this repo: `/sdlc:release` for the next version leaves `uv.lock` showing the new version,
  and a `uv run` afterwards changes nothing.
- A host that sets no such command releases exactly as today.
- `sdlc.py release --check` still writes nothing and runs nothing, and shows the command it would
  run.
- If the command fails, release stops before the commit and leaves the tree as it found it, the
  way a failed commit does now.

## Affected

- **Area:** the release loop. That's `cmd_release` in `scripts/sdlc.py`, the `/sdlc:release`
  skill, and the config table.
- **Files & components:**
  - `scripts/sdlc.py`: `cmd_release` gets a new step between `changelog` and `commit`.
    `CONFIG_KEYS` and `load_config()` get the new key.
  - `skills/release/SKILL.md`: its WAIT names the command.
  - `docs/REFERENCE.md`: the key.
  - `.sdlc/config.toml`: this repo sets it.
  - Tests in `tests/` for release.
  - `.sdlc/setup.json`: `record`, because the 008 gate fails on a `new` config key until it's
    recorded.
- **Downstream:**
  - Every host that runs `/sdlc:release`.
  - `drift`, which reports the new key as `new` to hosts already set up, through `/sdlc:setup`.
  - `cmd_publish` pushes the release commit as is.
- **Contracts:**
  - "Only publish pushes": the command must not push.
  - "Mechanism vs. policy": the plugin doesn't know a host builds with uv. The host names the
    command, the way `commands.check` and `retro.evidence` work.
  - Narrow `allowed-tools` and one WAIT per writing skill: the command runs inside `sdlc.py`, so
    the skill's rules don't grow, but the WAIT must show it.
  - `RETIRED_KEYS` / `TEMPLATE_READS`: no rename, so no entry.

## Constraints

- A release stays local and undoable with the `undo` it prints
  (`git tag -d … && git reset --keep HEAD~1`).
- Every refusal is still found before anything is written. The command itself can only fail at
  run time, so a failure there must roll back the bump and the changelog.
- Nothing outside what the command changed and what release already writes gets committed.
  Unrelated changes in the tree must not be swept in.

## Open questions

- ~~What is the key called, and where does it live?~~ Resolved: `release.after_bump`, beside
  `release.publish`, with the same `{version}` and `{tag}`.
- ~~How does release know which files the command changed?~~ Resolved: by comparing tracked files
  before and after. Release already refuses a main checkout with uncommitted tracked changes, so
  every tracked file the command changed is its own. New untracked files are reported, never
  committed.
- ~~Should `release` refuse up front when a version file's lock is already out of step?~~
  Resolved: no. The plugin can't tell what "out of step" means for a host's tool, and the command
  fixes it at the next release.
- ~~Should the 1.1.0 lock in this repo be fixed in this change?~~ Resolved: yes. This change
  commits `uv.lock` at 1.1.0 along with the key.
