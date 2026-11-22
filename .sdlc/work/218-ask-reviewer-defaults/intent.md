---
id: 218
slug: ask-reviewer-defaults
tier: 1
impact: patch
stage: shipped
created: 2026-11-21
opened: 2026-11-21T14:24Z
updated: 2026-11-22
shipped: 2026-11-22
idea:
depends_on: [216]
fixes: [2026-11-21-46]
serves: [O6]
origin: self
---

# 218 — `ask` says ship only when the build did what a confirmed default says

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From bug 2026-11-21-46: `factory.py ask NNN --answered <ids>` says `next: ship` whenever every
answer is `the assumed default, confirmed` (`cmd_ask()`, `KEPT_ANSWER`). But a reviewer's
`- DECISION:` line also carries a default ("Assuming yes"), and a reviewer doesn't build.
Confirming a reviewer's default is a choice of something the build may not do, so `ship` sends a
change to the landing without it.

On 216-autopilot the security reviewer raised D8 (`[review] sensitive` in the default guards) and
D9 (seeds with an `Issue:` line only when named in `--seeds`), and D10 (document the marker's
limit). None was built. `/sdlc-factory:decide 216` recorded all three as the assumed default,
confirmed, and `ask 216 --answered …,D8,D9,D10` printed `next: ship`. Only the supervisor reading
the code caught it, and the change was sent back with `/sdlc-factory:build`.

## Outcome

- `ask --answered` says `rebuild` (with `then` naming `/sdlc-factory:build NNN`, or `/sdlc:ship`
  on a READY) when any confirmed default was raised by a role that doesn't edit (a reviewer, the
  approver) and no builder report after it says it built it; it names those lines.
- A confirmed default the builder raised still reads as kept, as today, so a run of builder
  defaults still goes straight to `ship`.
- A test drives 216's case: a reviewer's default confirmed with no later builder report → `rebuild`;
  the builder's own default confirmed → `ship`.
- **Moves O6:** a factory change no longer lands with a confirmed call the build never made; the
  person's confirmation means what it says.

## Affected

- **Area:** the factory's decide path.
- **Files & components:** `plugins/factory/scripts/factory.py` (`cmd_ask()`, the ledger's `source`),
  `plugins/factory/skills/decide/SKILL.md` (what `rebuild` says), the factory's decide tests.
- **Downstream:** `/sdlc-factory:decide`, and 216's autopilot, which answers defaults through the
  same `KEPT_ANSWER` path.
- **Contracts:** none of the always-Tier-2 kind; `ask`'s `next` values are unchanged, only when
  each is given.

## Constraints

- `ask` stays read-only, and decides from the ledger and the rounds alone, never a model's reading.
- A builder's own default confirmed must not start sending changes back.

## Open questions

- How does the script tell a reviewer's default was built later: a builder report's `- DECISION:`
  line naming it, a `built D8` line the builder writes, or any builder report after the round that
  raised it?
- Should autopilot (216) treat such a line the same way, holding the change instead of landing it?

## Approach

Classify each answered default by its `source` role. In `cmd_ask()`, a `KEPT_ANSWER` on a line whose
source isn't the builder counts as kept only when a later builder report names that id as built;
otherwise `next` is `rebuild` and the lines are listed. Update the decide skill's `rebuild` wording
to say why, and add the test above.
