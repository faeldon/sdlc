---
id: 234
slug: autopilot-first-run
tier: 1
impact: none
stage: shipped
created: 2026-11-22
opened: 2026-11-22T10:50Z
updated: 2026-11-23
shipped: 2026-11-23
idea:
depends_on:
serves: [O6]
origin: self
---

# 234 — Turn on autopilot for its first run, one gate at a time

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

M25, from the retrospective of 2026-11-22, plans one bounded autopilot run on the nit paydown
seeds 2026-11-22-49, -50 and -51. The run can't begin. `factory.py autopilot --preview` reports
`"enabled": false`, because `.sdlc/factory.toml` has no `[autopilot]` section, and autopilot
refuses `--begin` until the base branch sets `enabled = true`.

The same file also sets `gate_jobs = 2`, by hand, in d039b1b. During the last window, two gates
at once filled the machine's swap:

- the gate's round median rose from 158.5 to 261.5 seconds;
- the slowest 15% of gates waited 648.5 seconds for a slot.

An unattended run building up to three changes at once (`parallel = 3`) would gate under the same
pressure, with nobody watching.

## Outcome

- On main, `.sdlc/factory.toml` sets `gate_jobs = 1` and has an `[autopilot]` section with
  `enabled = true`. Its header comment says why, and that both settings are for M25's run.
- From the main checkout, `factory.py config` shows `gate_jobs` as 1, and `factory.py autopilot
  --preview --seeds 2026-11-22-49 2026-11-22-50 2026-11-22-51` shows `"enabled": true`.
- `./check.sh` passes.
- **Moves O6:** autopilot can run its first bounded goal, so what it lands can be read beside the
  supervised factory's.

## Affected

- **Area:** this repo's own factory settings.
- **Files & components:** `.sdlc/factory.toml` alone.
- **Downstream:** `factory.py` reads the file from the base branch. `gate_jobs` is read by every
  factory gate and by the hand gate's slots (`_hand_slot()`), and `[autopilot]` by autopilot's
  `--begin`. No host reads this file. Autopilot's other keys (`parallel`, `wait`, `debt`, `risk`,
  `guards`) keep their defaults.
- **Contracts:** none. It waits on no open change.

## Constraints

- **Nothing runs until it lands.** The file is read from the base branch, so the settings take
  effect only once on main, and this change starts no autopilot run.
- **One gate at a time is slower for a batch.** Gates queued for up to half an hour before d039b1b.
  That's the trade M24's 2026-11-22-38 is meant to remove.
- **No guard is loosened.** `guards` stays unset, so autopilot still holds anything touching the
  policy and review docs or a `[review]` sensitive or irreversible path.

## Open questions

- Should `enabled` go back off after the M25 run, until a retrospective has read what it landed?
- Only -49 is in `status`'s ready group now. -50 and -51 are in "decide", which autopilot never
  takes. Does the run take them once -49 is opened, or do they need to be made ready first?

## Approach

1. In `.sdlc/factory.toml`, set `gate_jobs = 1` and add `[autopilot]` with `enabled = true` and a
   comment naming M25.
2. Rewrite the header comment's account of `gate_jobs`, which now says "two gates at once".
3. Run `./check.sh`.

The `factory.py config` and `autopilot --preview` checks read the base branch, so they're run from
the main checkout after close.
