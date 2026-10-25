---
id: 013
slug: landing-reach
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 013 — Close says what a landed plugin change needs from open sessions and hosts · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `_change_base()` lifted out of `_change_diff()` (the parent of the commit
  that first holds the intent, stable across the fast-forward, a rerun and a handoff);
  `landing_reach(paths)`, pure, sorting paths into `scripts`, `skills` (namespaced:
  `sdlc:ship`, `sdlc-factory:build`), the factory's `agents` (`sdlc-factory:reviewer-code`,
  read at session start like skills) and `hosts` (`defaults/`, `templates/`); `_reaches()`
  wrapping it over the branch's diff, never a refusal, `{"unknown": <why>}` when it can't read
  the paths so "nothing to do" is never a guess; `cmd_close()` sets `report["reaches"]`
  before its steps, only when `_own_repo()` and the change is shipped.
- `skills/close/SKILL.md`: Step 4 reports `reaches`, one line per key, and nothing when absent.
- `docs/CONTRIBUTING.md`: `### When a change lands` under "Working from a clone".
- `tests/test_archive.py`: `landing_reach()` cases, an own-repo close that reports skills and
  hosts, one that reports none, and a host close that never has `reaches`.

## Work order

1. `_change_base()`, with `_change_diff()` calling it; the measure tests still pass.
2. `landing_reach()` and its parametrized test.
3. `_reaches()` and the `cmd_close()` entry, with the close tests.
4. Close's Step 4 and the CONTRIBUTING section.

## Tests

- Kinds from paths: `test_landing_reach_sorts_paths_into_what_each_needs` (script only, factory
  script, skills, factory skill, factory agent, setup's files, a mix, none).
- `test_a_close_that_cant_read_the_changes_paths_says_so`: `unknown` with its reason, and the
  close still lands.
- In close: `test_the_plugins_own_close_reports_what_reaches_its_sessions`,
  `test_a_change_that_reaches_nothing_reports_no_reaches`, and
  `test_a_host_repo_never_hands_off` asserting no `reaches`.
- Manual: once shipped, `sdlc.py close 013 --check` from the main checkout shows `reaches` with
  `scripts` and `sdlc:close`.

## Rollback

`git revert <sha>` covers it all: close writes nothing new, the entry is report output only.
