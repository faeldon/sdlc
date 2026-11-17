---
id: 076
slug: readme-factory-and-manual
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
serves: none
---

# 076 — Say in the README that the factory and manual mode mix, change by change

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The README presents the factory as an optional feature, but never says that it and manual mode
work side by side in one project, change by change. A host reading it can't tell whether
installing `sdlc-factory` commits every change to the factory, or whether a change can start by
hand and be built by the factory (or the other way round). It is nice to know that you can
intermix the skills, creating some features by hand and some with the factory in the same
project.

## Outcome

`README.md`'s **Optional features** list has a bullet, after the factory's, saying: every change
starts with `/sdlc:intent` and the next command decides how it is built; the two paths side by
side in a small table; that a change can switch partway (a spec by hand then the factory's build
from `stage: design`, or a factory build shipped by hand with `/sdlc:ship`); that both kinds run
side by side in their own worktrees, numbered from one counter; and that each is measured as it
was built (`Sdlc-Mode: factory` or `manual`), so retrospectives can compare the two.

## Affected

- **Area:** the root README, the doc a host reads first.
- **Files & components:** `README.md` only.
- **Downstream:** people reading the README; no script or test reads this section.
- **Contracts:** none.

## Constraints

- Say only what the plugin does today: `/sdlc-factory:land` takes only ready factory changes; a
  change built by hand always ships with `/sdlc:ship` and `/sdlc:close`.
- Nothing that cites a project or a machine (`tests/test_nothing_local.py`).

## Open questions

None.

## Approach

Add one bullet to `README.md`'s **Optional features**, after the factory bullet:

- **Factory and manual, change by change.** Installing the factory changes nothing for the
  changes you build by hand: every change starts with `/sdlc:intent`, and the command you run
  next decides how it's built. You can mix them in one project, and switch partway through:

  | Step | By hand | With the factory |
  |---|---|---|
  | Spec (Tier 2) | `/sdlc:spec` | drafted inside `/sdlc-factory:build`, approved at its gate |
  | Plan and build | plan mode, then you | `/sdlc-factory:build` |
  | Ship and close | `/sdlc:ship`, `/sdlc:close` | `/sdlc-factory:land`, or `/sdlc:ship` and `/sdlc:close` |

  Write the spec yourself and hand the build to the factory (it starts from `stage: design`), or
  have the factory build a change and ship it yourself (`/sdlc:ship` shows the agents' verdicts
  beside its own review). Each change keeps its own worktree, so factory and hand-built changes
  run side by side, numbered from the same sequence (the tracker's issues, or the local counter).
  Each is measured by how it was actually built (`Sdlc-Mode: factory` or `manual` on its `Close`
  commit), so retrospectives can set the two ways side by side.

No other file changes; the gate covers it (`test_nothing_local.py` and the doc-shape tests read
every tracked file).
