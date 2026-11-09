---
id: 045
slug: release-when-due
tier: 1
impact: minor
stage: shipped
created: 2026-11-09
updated: 2026-11-09
shipped: 2026-11-09
idea:
depends_on:
serves: [O3]
---

# 045 — Status recommends a release only once a batch is due

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:status` recommends `/sdlc:release` as soon as one closed change is unreleased: rule 5 of
its precedence (`skills/status/SKILL.md:145`) fires on any `Unreleased` line, one `impact: none`
change included, and it outranks every Next up line, `Priority: high` too. The process guide says
to release "once per batch of closed changes" (`guide/process.md:111`) and "after a few of
those" (`guide/process.md:533`), but nothing says how big a batch is, so the recommendation
starts after a change or two. On 2026-11-08, with 042, 043 and 044 closed (one of them `none`),
status put the release ahead of the five ideas just marked `Priority: high`.

It costs twice. Hosts reading the plugin from a clone already have every landed change, so an
early release gains them nothing. And `retro.after_releases` counts releases, so a release every
change or two makes a retrospective due every few changes.

## Outcome

- `status` shows **Release due** with why, as it shows **Retro due**, once the unreleased batch
  reaches a threshold: 5 changes of `impact: minor` or higher, or 1 `major`, or the oldest
  unreleased `Close` commit 14 days old. Below it, `Unreleased` still lists the changes and the
  next version, with no `/sdlc:release` call to action.
- The status skill recommends a release only when it is due, and only after any `Priority: high`
  Next up line: urgent work first, then a due release, then the rest of the backlog.
- Each threshold is a `[release]` key in `.sdlc/config.toml`, documented in `docs/REFERENCE.md`
  beside `retro.after_releases`, with 0 turning that rule off.
- `/sdlc:release` itself never refuses below the threshold: a person can release whenever they
  choose.
- Today: 042 and 044 are `minor` and 043 is `none`, 2 of 5, the oldest closed 2026-11-07, so
  status says nothing is due until 2026-11-21.
- **Moves O3:** the person reaches the change they mean to work on without a release
  recommendation in front of it, and retrospectives come due by real batches.

## Affected

- **Area:** `status` and its skill, the `[release]` config, and the docs that say when to release.
- **Files & components:** `scripts/sdlc.py` (a `release_due()` beside `retro_due()`, its
  `[release]` defaults and `INT_KEYS`, `status`'s JSON and print, `unreleased()`'s report);
  `skills/status/SKILL.md` (Step 3's precedence and what Unreleased means); `docs/REFERENCE.md`
  (the config block and What comes next); `guide/process.md` (the Release row, and "after a few
  of those"); the README if it says when to release; tests in `tests/test_release.py` or
  `tests/test_next_up.py`.
- **Downstream:** every host's `status`, at once for hosts reading the plugin from a clone, at
  the next release for the rest. No host's files change: the keys are optional with defaults.
- **Contracts:** status is read-only; `check --strict` is a gate; the scripts run on Windows.

## Constraints

- Status stays read-only, and `check --strict` stays a gate: a due release is never a problem.
- Impacts come from history as `unreleased()` reads them now; nothing re-derives one.
- `release.version_files` unset or a missing tag behave as now: those are `configure` and
  `missing`, never "not due".
- The scripts run on Windows; dates come from git's commit times, not a file's.

## Open questions

- ~~Is a `Priority: high` *bug* also ahead of a due release?~~ Resolved: yes, any line marked
  `priority high`, bug or idea, comes before it.
- ~~Should a closed change with a `closes:` issue, which waits on a push to close, make a release
  due sooner?~~ Resolved: no, that waits on a push, which is publish's (`2026-10-25-19`).

## Approach

1. `release_due(home, cfg, unreleased)`: counts changes with impact `minor` or `major`, any
   `major`, and the age of the oldest unreleased `close_date`; returns `{due, why}` like
   `retro_due()`.
2. Config `[release]`: `due_after_changes = 5`, `due_after_days = 14`; a major is always due.
   Both are `INT_KEYS`, and 0 turns one off.
3. `status` prints `Release due: <why>  /sdlc:release` when due, and moves `/sdlc:release` off
   the Unreleased line when it isn't, so the call to action shows only when it applies.
4. The status skill's precedence becomes: problems, Ready to close, quiet build+, quiet
   depended-on, `Priority: high` Next up, **Release due**, Retro due, the first Next up line.
5. Docs and tests: a batch below the count, at it, a major alone, an old batch, and each key at 0.
