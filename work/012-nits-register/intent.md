---
id: 012
slug: nits-register
tier: 2
impact: minor
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea: Carry a ship's unfixed nits forward
depends_on:
serves: [O2, O4]
---

# 012 — A ship's unfixed nits are kept, weighed and paid down by theme

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Ship ranks findings Important or Nit. An Important blocks the commit; a nit approved unfixed
survives only as a number in the `Sdlc-Findings` trailer. What it was, where it lives and why it
was left go nowhere anyone reads again. Nine are open today, remembered only by the seed's prose:

- 003: a status test whose patched half can't fail; a registry that crashes `status` when it isn't
  UTF-8.
- 005: `left` builds up across checks; timeout output kept as bytes; checks inherit stdin.
- 009: the `RECORD_CLEARS` tuple-unpacking idiom.
- 010: `git diff --name-only` misses files the after-bump command stages; a changelog section isn't
  rolled back when `after_bump` fails, so a rerun writes it twice; two release-skill lines run past
  100 characters.

Carrying each as a `work/ideas.md` seed, the way ship carries undone items, isn't the answer either.
Most nits cost more to fix alone than they're worth: they move no outcome in the product doc, and
a seed apiece would bury the ideas that do. In the originator's words, nits are small technical
debts: they should be kept somewhere they can be revisited, judged by a rubric on whether fixing
them is worth it, and paid down in bulk, like with like (documentation, refactoring, robustness
from edge-case handling), not one change per nit. Some are made moot by later changes, and nothing
notices.

## Outcome

- Ship writes each nit approved unfixed to a register, `work/nits.md`, apart from the seeds, with
  structured fields: an id, the date raised and the change that raised it (so its age reads off),
  the review pass, a theme (docs, refactor, robustness, …), the paths it touches, and a rubric
  score for cost against value to the product doc's outcomes.
- The rubric lives in the process doc, so whether a nit is worth fixing is judged the same way each
  time, not argued afresh at each ship.
- At intent, spec and toward planning, the stage lists open nits touching the same paths or theme
  and offers to take the cheap ones into the change, so changes shave the pile as they pass.
- Before ship's WAIT, ship lists open nits the diff touches and proposes retiring those it fixed or
  made moot; retired nits leave the register in the ship commit, and history keeps them.
- A retrospective reports open nits by theme and age, and proposes one change to pay down a theme
  once it crosses a threshold.
- Release and publish neither read nor clean the register: the release cycle is for shipping
  features, and the in-change and retro loops already cover cleanup.
- The nine above are in the register, and this seed leaves `work/ideas.md`.
- **Moves O2:** a nit approved unfixed is never lost: each is in the register until fixed or
  retired, and history shows which.
- **Moves O4:** the retrospective decides whether to pay down debt from the register's counts and
  ages by theme, not from memory.

## Affected

- **Area:** the ship, intent, spec and retro skills; `scripts/sdlc.py`; the process docs.
- **Files & components:** `skills/ship/SKILL.md` (capture and retire), `skills/intent/SKILL.md` and
  `skills/spec/SKILL.md` (pickup), `skills/retro/SKILL.md` (weighing); `scripts/sdlc.py` (a `nits`
  subcommand to list, add and retire, text-only parsing, retro's counts); a new `templates/nits.md`;
  `defaults/SDLC.md` and `.sdlc/SDLC.md` (rubric and themes), maybe the review docs; tests in
  `tests/test_skills.py`, `tests/test_sdlc.py`, `tests/test_defaults.py`.
- **Downstream:** every host (ship's output and commit gain a register write), `/sdlc:retro`'s
  report, and the `Sdlc-Findings` trailer, which retro already counts and must keep meaning.
- **Contracts:** ship's and retro's WAITs gain an effect; a new file `sdlc.py` writes in a host;
  `templates/` shape rules (`tests/test_defaults.py`); defaults mirrored into `.sdlc/`, and `record`
  after editing `defaults/`; the trailer format, which metrics only ever extends.

## Constraints

- `Sdlc-Findings` keeps its format and meaning; retro's counts from it and from history don't move.
- Release and publish don't touch the register.
- A host that never leaves a nit unfixed sees no new file and no new step.
- Ship stays one WAIT: capture and retirement are part of what it approves, not new stops (O3).
- Pickup at intent and spec is an offer, never automatic: the person decides what a change takes.
- Register entries are parsed as text, never through YAML (`frontmatter_list()`'s rule).

## Open questions

- ~~One change, or several (register and ship capture first, then pickup, then retro)?~~
  Resolved: one; the register's shape is what every stage reads. Plan mode may still split it.
- ~~The rubric: which axes (cost, value against outcomes, risk, age), and what score sends a nit to
  a seed or straight into the next change?~~ Resolved: cost S/M/L and value med/low; high value
  isn't a nit, L goes to a seed, S with med is offered for fixing at ship (spec, Design).
- ~~Themes: a fixed list in the plugin, or host-defined in config or the process doc? A per-feature
  category was judged hard to design here; is theme plus paths enough?~~ Resolved: free text with a
  default list in the process doc; paths stand in for features.
- ~~The retro threshold for proposing a paydown change: count per theme, age of the oldest, or
  both?~~ Resolved: both, as process-doc prose (5 per theme, or older than 60 days).
- ~~Location and shape: one `work/nits.md` list, or a file per nit? Does setup create it, from
  `templates/`?~~ Resolved: one list from `templates/nits.md`, written by ship when first needed.
- ~~Plan mode isn't a skill: can anything prompt pickup there, or do intent and spec carry it
  alone?~~ Resolved: intent (Tier 1) and spec (Tier 2) carry it.
- ~~Does ship also offer to fix a cheap nit in the diff before committing, or only capture it?~~
  Resolved: only capture; "fix a finding first" is already the person's answer at its WAIT.
