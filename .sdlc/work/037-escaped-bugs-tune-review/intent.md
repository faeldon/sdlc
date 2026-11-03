---
id: 037
slug: escaped-bugs-tune-review
tier: 2
impact: minor
stage: shipped
created: 2026-11-04
updated: 2026-11-04
shipped: 2026-11-04
idea: 2026-11-03-7
depends_on:
serves: [O4]
---

# 037 — Retro tunes the review from the bugs that got past it

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Retro already lists each escaped bug's introducing change with its tier (`bugs_retro()`'s
`escapes`), and stops there:

- **It doesn't say what the review saw.** That change's `Sdlc-Findings` trailer is in history, and
  since 035 its `findings.md` too, each finding with its class and disposition. Retro never pairs
  them, so "which layer should have caught this" goes unasked: a pass that found nothing, a finding
  answered `wrong` or `minor` that was the bug, a class nobody looks for.
- **Nothing feeds the review doc's failure classes.** `guide/review.md`'s "The ways this repo's
  code fails" is the slot for a host's own classes. Retro's Process pass proposes a missed class
  only as an intent title, so the slot fills by hand or not at all. Recurring Important findings
  of one class aren't proposed either, as a lead, a lint rule or a test.
- **Escapes rising changes nothing.** 036 made review depth configurable (`[review] sensitive`,
  the fresh reviewer), but retro, which sees escapes per closed change across windows, never
  proposes moving a path onto the sensitive list when they rise, or easing off when they hold.

This takes in seeds 2026-11-03-7 and -8 together, as phase 3.

## Outcome

- `sdlc.py retro`'s `bugs` part gives, for each escape, the introducing change's review: the
  trailer's counts, and from its `findings.md` in history, the findings on the bug's `Paths:` with
  their class and disposition, or that it had none.
- Retro gives the escape rate (bugs introduced per closed change) for this window beside the last,
  and which way it moved.
- The retro skill proposes, behind its one WAIT, each missed or recurring class as a `- **lead**`
  for the review doc's "ways this repo's code fails"; and, when escapes rose, a tightening (a path
  onto `[review] sensitive`, the fresh review always on, a class made blocking), or when they held,
  a loosening, each citing the escape and the review that missed it.
- Seeds 2026-11-03-7 and -8 both leave the register when this ships.
- **Moves O4:** the review changes a retrospective proposes cite the bugs that got through and the
  review that missed them, not process counts alone.

## Affected

- **Area:** retro (script and skill), the review doc, `[review]`.
- **Files & components:** `scripts/sdlc.py` (`bugs_retro()`, `closed_changes()` reading a change's
  `findings.md` from history, `retro()`, perhaps `cmd_retro_commit()`'s allowed paths),
  `skills/retro/SKILL.md` (the Process pass and its WAIT), `guide/review.md`, `guide/process.md`,
  `docs/REFERENCE.md`, `AGENTS.md`, tests in `test_retro.py` and `test_skills.py`.
- **Downstream:** every host's retro. A host with no bugs, or none with `Introduced by:`, retros
  exactly as now.
- **Contracts:** retro read-only until its WAIT and one commit through `retro-commit`; a skill's one
  WAIT; `findings.md`'s format from 035, read, never redefined; escapes matched with
  `names_change()`; the register's bugs stay `/sdlc:bug`'s to file and retire.

## Constraints

- Retro proposes, never decides: every edit to the review doc or `[review]` passes its WAIT.
- An escape whose introducing change predates `findings.md` reads as "review unknown", never as
  "the review found nothing".
- Few escapes are anecdote: the rate and any tightening say how many changes they rest on.

## Open questions

- ~~Does retro write the review doc and `config.toml` itself at its WAIT (widening `retro-commit`'s
  allowed paths), or propose each as a seed for a change to make?~~ Resolved: a seed holding the
  exact text, the person's call; `retro-commit` unchanged (spec R6–R8).
- ~~How is a bug matched to a finding: by `Paths:` overlapping the finding's `Evidence:`, by class,
  or only shown side by side for the person to judge?~~ Resolved: by paths, mechanically
  (`on_paths`), with `Sdlc-Fixes` gaining `paths=`; the class is the skill's judgment (spec R1–R3).
- ~~What counts as "rose": a threshold, a minimum of closed changes, or the person's judgment from
  the two numbers?~~ Resolved: the window's rate against the previous one's, `unknown` under five
  closed changes in either (spec R4).
- ~~Can retro read a closed change's `findings.md` from history cheaply, from the `Close` commit's
  parent as `closed_changes()` reads the intent?~~ Resolved: yes, one `git show` of the change's
  own commit (spec R2, R5).
