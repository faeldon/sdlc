---
id: 111
slug: factory-loose-ends
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-19, 2026-11-17-64, 2026-11-17-67, 2026-11-17-80]
depends_on:
serves: [O6]
---

# 111 — Close four small gaps in the factory

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Four small gaps in the factory, each left by a change that landed today:

- **2026-11-17-19:** `factory.py`'s `_free_port()` picks a port for the UI review's dev server and
  releases it before the outside `[ui] serve` command binds it, so a parallel run could take it in
  between. 089 closed the same window in the board's tests by serving on port 0.
- **2026-11-17-64:** `/sdlc-factory:spec` gets `start`'s `base` and `behind` keys (101) but doesn't
  show them, and doesn't run `fresh`, so a spec can be drafted on a stale branch.
- **2026-11-17-67:** the build skill's summary of `start`'s `ui` (`serve`, `shoot`, `paths`)
  doesn't name `fixture`, which the README does.
- **2026-11-17-80:** `_resolve()`'s problems still say "round <n>" for a landing round's answer ("C3,
  which no change of round 1 is"). Only the file named before them says which kind of round it is.

## Outcome

- The UI review's server can't lose its port to a parallel run: `factory.py` either retries a
  serve that fails to bind, or uses a port the serve command reports.
- `/sdlc-factory:spec` shows how far behind `main` the change is, and brings it up to date with
  `fresh` before the spec-writer drafts, as the build skill does.
- The build skill names `fixture` among `start`'s `ui` keys.
- `_resolve()`'s problems name a landing round as `land-<n>`, and a build round as `round <n>`.
- Tests in `tests/test_factory.py` and `tests/test_land.py` pin the port, the spec skill's
  `fresh` and the problem's wording.
- **Moves O6:** the factory finishes what it starts on a current branch, with no race to lose.

## Affected

- **Area:** sdlc-factory.
- **Files & components:** `plugins/factory/scripts/factory.py` (`_free_port()`, the UI review's
  server, `_resolve()`), `plugins/factory/skills/spec/SKILL.md`,
  `plugins/factory/skills/build/SKILL.md`, `tests/test_factory.py`, `tests/test_land.py`.
- **Downstream:** every factory run with `[ui]` set, and every factory spec.
- **Contracts:** `fresh` is one of the named writes before a WAIT (AGENTS.md); running it from the
  spec skill too keeps it to the change's own branch, and leaves the worktree as it was on a
  conflict.

## Constraints

- The `[ui] serve` command stays the host's: no change to what a host writes in `[ui]`, unless
  the port design needs a new placeholder, which is then optional.
- `fresh` from the spec skill must be the same call the build skill makes, with its own rule.

## Approach

Retry the serve, once or twice, on a new port when the server doesn't come up on the one picked,
and say so in the review's record. Have the factory spec skill run `start` and `fresh` as the
build skill does, show `behind` in its question, and stop on a conflict. Add `fixture` to the
build skill's line. In `_resolve()`, take the round's kind from the file it reads and word
`land-<n>` for a landing round.

## Open questions

- Retry on a new port, or let `[ui] serve` report the port it bound (`{port}` = 0)? The Approach
  retries; reporting needs every host's serve command to cooperate.
