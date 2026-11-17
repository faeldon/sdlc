---
id: 092
slug: retro-outcome-coverage
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-4
depends_on:
serves: [O4]
---

# 092 — Retro checks its goals and the work against the outcomes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Retro's product pass (`skills/retro/SKILL.md`, pass 4) scores each open outcome against the
evidence, and `_product()` (`scripts/retro.py:146`) lists the closed changes that serve `none`.
Nobody asks the reverse question: do the outcomes still cover the work, and does the direction
still answer to the outcomes?

The last retrospective (2026-11-17) shows both gaps.
- **The work outran the outcomes.** 8 of the window's 27 changes served `none`. Most were cost and
  cleanup work the person counts as important, so a real aim has no outcome to say whether it's
  being met. `product.none` lists them by name only, and the skill's "a share of `none` … that
  keeps growing is a finding" never says what to do about it.
- **The direction doesn't answer to the outcomes.** The goals cite outcomes only by habit
  (`G6. … (O2)`). `templates/direction.md` asks for no citation and `direction_items()` reads
  none. No milestone names a goal or an outcome at all. M12 (Each rule is said once) was drafted
  with neither behind it, and nothing flagged that.

## Outcome

- **Moves O4:** every goal and milestone a retrospective writes answers to an outcome, and
  recurring work outside the outcomes becomes a proposed outcome the person approves, rather than a
  growing `none` count.
- The direction doc has a form for what each goal and milestone answers to. `direction_items()`
  reads it, and `templates/direction.md` asks for it.
- `retro`'s `product` block names the open goals and milestones that cite no outcome (directly, or
  through their goal), and groups the `none` changes by theme, so the skill doesn't group them by
  hand.
- The product pass names the uncited items, and where a theme of `none` changes keeps recurring it
  proposes a new `O<n>` outcome line (from `product.next_ids`) at the retrospective's existing
  WAIT. Its question already covers outcome lines, so what it approves is unchanged.
- `./check.sh` passes.

## Affected

- **Area:** the retro loop.
- **Files & components:** `scripts/retro.py` (`_product()`), `scripts/sdlc.py`
  (`direction_items()`, perhaps `register_drift()`/`retro-commit`'s checks),
  `templates/direction.md`, `skills/retro/SKILL.md` (passes 4 and 5), `.sdlc/DIRECTION.md` (this
  repo's own milestones gain citations at its next retrospective), and `tests/`.
- **Downstream:** every host that runs `/sdlc:retro`. Its direction doc gets a new form, and its
  retro output a new field. `status` reads `direction_items()` for Next up, so that reading must
  not change for a doc without citations. `templates/` is an `irreversible` path in this repo's
  review config.
- **Contracts:** AGENTS.md's *Retrospectives*: `retro` stays read-only, `cmd_retro_commit` writes
  only the direction doc, the inbox and the product doc's outcome lines, and refuses a doc that
  drops an open id. *One shape for the shipped docs* (`tests/test_defaults.py`) binds the
  template. Frontmatter and ids are read as text.

## Constraints

- A host's existing direction doc, with no citations, still reads exactly as before: uncited items
  are reported, never refused.
- Retro proposes, and the person decides at the WAIT. No outcome is added, and no citation written,
  without that yes.
- Retro never edits the product doc's users, problem, measures or bets, only its outcome lines.
- A new field in `retro`'s JSON is added beside the old ones, never in place of them.

## Open questions

- ~~What form does a citation take: the trailing `(O1, O3)` this repo's goals already use, a
  `Serves:` line under each milestone beside `Groups:`, or a milestone naming its goal (`(G7)`) and
  inheriting the goal's outcomes?~~ Resolved: a goal ends with `(O1, O3)`; a milestone has a
  `Serves:` line beside `Groups:` naming its goal, outcomes or both (spec R1, R2).
- ~~Where does a closed change's theme come from? Changes have none. Their seeds' `Theme:` lines are
  gone from the register by close, so they would have to be read from history (the inbox at the
  change's parent commit), or intent would have to record a theme of its own.~~ Resolved: its
  seeds' `Theme:` lines, read from the register at the change's base (`Sdlc-Base`) (R6).
- ~~What counts as "keeps recurring": a theme with N `none` changes in one window, or across two
  retrospectives?~~ Resolved: 3 `none` changes under one theme in one window (R7).
- ~~Should `retro-commit` refuse a new uncited goal or milestone, or is reporting it enough?~~
  Resolved: reported, never refused (R3, R5).
