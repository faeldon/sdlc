---
id: 108
slug: resolve-markers
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
fixes: [2026-11-17-51]
serves: [O6, O3]
---

# 108 — A resolve matches conflict markers as whole lines

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From bug 2026-11-17-51: `factory.py resolve --continue` and `sdlc.py resolve` refuse "conflict
markers left in" any conflicted file that holds a run of seven less-than signs anywhere, and both
scripts hold one in their own marker check. So a conflict in `factory.py` or `sdlc.py` is refused
though nothing is left, and so is any text quoting the run, as bug 51's own first wording did in
the register. On 2026-11-17 it stopped six landings (103, 098, 102, 105, 104, 107), each finished
by hand after a check for whole-line markers.

## Outcome

- Both checks match a marker only as a whole line: seven less-than signs and a space, seven equals
  signs alone, or seven greater-than signs and a space.
- A conflict in `factory.py`, `sdlc.py` or a register quoting the run continues cleanly; a real
  marker is still refused.
- A test runs each script's check on its own source and on a file holding a real marker.
- **Moves O6:** a landing doesn't stop on a correct resolution.
- **Moves O3:** no hand finish of a rebase.

## Affected

- **Area:** conflict resolution in sdlc and sdlc-factory.
- **Files & components:** the marker checks in `plugins/factory/scripts/factory.py` and
  `scripts/sdlc.py`; `tests/test_resolve.py`, `tests/test_land.py`.
- **Downstream:** `/sdlc:ship`'s conflict branch and every factory landing.
- **Contracts:** `factory.py` never imports `sdlc.py`; its copy of the check is pinned to
  `sdlc.py`'s by a test.

## Constraints

- A real marker is never accepted.

## Open questions

- None.

## Approach

One line-anchored pattern in each script, a test pinning the factory's copy to `sdlc.py`'s, and
tests over each script's own source and a file with a real marker.
