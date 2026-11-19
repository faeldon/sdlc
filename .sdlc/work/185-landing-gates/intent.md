---
id: 185
slug: landing-gates
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T12:59Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-19-58
depends_on:
fixes: [2026-11-19-61]
serves: [O3, O6]
---

# 185 — The landing runs every gate a hand-built change gets, and stops only for what wasn't approved

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two gaps in what the landing runs. Idea 2026-11-19-58: "Today the train stops at `accept` every
time a change has acceptance checks, because the loop never runs a host command and only a session
can prompt; the person must rerun /sdlc-factory:land just to click through checks whose commands
they approved word for word in the landing question." Today every train of 177, 178 and 180
stopped there once. Its proposal: record a hash of each change's `checks.md` at `train --begin`
and let the loop run `accept` itself while it is unchanged; when it changed, run it only when the
approver judges the change harmless and the script finds only allow-listed read-only programs.

Bug 2026-11-19-61 (med): "The factory runs only `commands.check`, through `_run_check()` …:
neither a build round's gate nor a landing train's gate at the tip runs `commands.build`, so a
factory-built change that touches those paths lands without the slow gate the same change built by
hand would get at ship."

Three nits on the same code come in: 2026-11-19-47 (the land-fix refusal message is long and
repeats `FIX: ALREADY MADE`), -48 (`taken_lines()` reads every indented line after `Nits taken in:`
as part of it, so a sub-bullet naming an id it leaves out retires it) and -36 (`purpose_of()`'s
docstring doesn't say a run with no figures writes no row).

## Outcome

- A train runs a change's acceptance checks as stacked without stopping while its `checks.md` is
  the one the person approved; a changed one runs unattended only when the approver and the
  script's read-only allow-list both clear it, and otherwise stops as today, with the reason.
- When a change's diff matches `build_when` or a sensitive path, the factory runs `commands.build`
  too, at least once before it lands, recorded like the gate.
- The three nits are fixed or answered.
- **Moves O3:** a landing with acceptance checks no longer stops for a click on what was approved.
- **Moves O6:** a factory-built change gets every gate a hand-built one gets.

## Affected

- **Area:** the factory's landing and its gate.
- **Files & components:** `plugins/factory/scripts/landing.py`, `plugins/factory/scripts/factory.py`
  (`_run_check()`, `taken_lines()`, `purpose_of()`), the approver's landing prompt,
  `plugins/factory/skills/land/SKILL.md`, `plugins/factory/README.md`, `tests/test_train.py`,
  `tests/test_land.py`.
- **Downstream:** every factory landing; any host that sets `commands.build`.
- **Contracts:** "a host command runs only behind a prompt" becomes "behind the person's yes for
  that exact command"; `[review] sensitive` covers `landing.py`, so full depth.

## Constraints

- A check whose command changed never runs unattended on the approver's word alone.
- `commands.build` is never run for a host that doesn't set it.
- The run lock and every existing stop stay as they are.

## Open questions

- ~~Does `commands.build` run on every build round, or only once at the landing's tip?~~ Resolved:
  once, at the landing train's tip (spec R13).
- ~~Exactly which programs and arguments are on the read-only allow-list?~~ Resolved: spec R5.
