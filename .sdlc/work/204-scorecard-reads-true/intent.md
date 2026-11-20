---
id: 204
slug: scorecard-reads-true
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-20T05:38Z
updated: 2026-11-20
shipped: 2026-11-20
idea: [2026-11-20-15, 2026-11-20-24, 2026-11-20-39]
depends_on:
serves: [O4]
---

# 204 — The scorecard's null rows and retire list read true

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Three seeds and a nit say the scorecard still reads untrue in places:
- 2026-11-20-15, left undone by 191: "`retro.py`'s workarounds block gives `unknown` a `count` and
  `rows` but no `n`, though `_workarounds()`'s docstring says 'each count carries its `n`'."
- 2026-11-20-24, left undone by 189: "The scorecard's lead-time rows by way still say `none in the
  window` when the window closed changes but none of that way. `no <way> change in the window`
  would match the escape rate's." Nit 2026-11-20-25 says the same.
- 2026-11-20-39 (raised by the retrospective of 2026-11-20): the surface's retire list names 33
  config keys unused for 3 windows, among them `git.base` and `git.push`, which every change reads
  and close pushes by. The measure counts a key as used only when something other than the config
  loader records it.

## Outcome

- The workarounds' `unknown` block carries its `n`.
- A lead-time-by-way row with no change of that way says `no <way> change in the window`.
- `git.base`, `git.push` and every key `load_config()` or a command reads on every run counts as
  used in the surface; the retire list keeps only keys nothing read.
- **Moves O4:** a retrospective's retire list and null rows can be acted on as they read.

## Affected

- `scripts/retro.py` (`_workarounds()`, the scorecard's lead rows, `surface`), `tests/test_retro.py`,
  `tests/test_surface.py`, `docs/FEATURES.md` if the surface's rules are said there.
- **What reads it:** every host's retrospective.

## Constraints

- `retro` stays read-only but for its report, and `surface` is built from the code, never a list
  kept by hand.
- An item no record could show stays `unmeasured`, never `unused`.

## Approach

Add `n` to `unknown` as the other blocks have it. Give the lead rows by way the escape rate's
reason. For the surface, find where a key is recorded as used, and count the keys a command reads
from `load_config()`'s resolved dict, by name, as used whenever that command ran in the window.

Nits taken in: 2026-11-20-25
