---
id: 104
slug: landing-follows-main
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-37, 2026-11-17-38]
depends_on: [097]
serves: [O3, O6]
---

# 104 — The landing follows main and reviews its own fixes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

- **2026-11-17-37:** "When another session lands a change between a landing's review and its close, `land --close` refuses (close only fast-forwards) and someone runs `base` by hand, then gates again." Hit by 094 and 095 on 2026-11-17.
- **2026-11-17-38:** "When the person asks for a fix after the approver (088's plan hint, 094's AGENTS.md line on 2026-11-17), the supervisor makes it by hand and the change lands `by=person` with no reviewer having read the fix."

## Outcome

- When `main` moves before a change's close, the landing goes back to its own rebase step, gates and reviews the change as it now stands, and closes, stopping only on a conflict it can't resolve or a red gate; a test moves `main` between review and close.
- A fix asked for at landing goes to the change's builder, and then to its reviewers at the run's depth, before it lands; a fix made any other way is recorded on the commit (`Sdlc-Landed: … unreviewed=<paths>` or a trailer of its own) so the retro can count it.
- **Moves O3:** no hand `base` and regate at landing.
- **Moves O6:** nothing lands that no reviewer read without the record saying so.

## Affected

- **Area:** sdlc-factory's landing.
- **Files & components:** `plugins/factory/scripts/factory.py` (`land`, `land --close`, `land-verdicts`), `plugins/factory/skills/land/SKILL.md`, `plugins/factory/README.md`, `tests/test_land.py`; `scripts/metrics.py` if a new trailer is added.
- **Downstream:** every factory landing; the retro's counts.
- **Contracts:** a skill's WAIT (what a landing's yes covers when it loops); the trailer format is a contract, extended, never redefined; landing commits only through `sdlc`'s own steps.

## Constraints

- A loop is bounded: after N moves of `main` it stops and says so.
- Never a merge of `main` into the branch, never `--force`.

## Open questions

- ~~Does a yes cover a re-gate and re-review after `main` moves, or does a moved change need the person again?~~ Resolved: the yes covers it, up to `[land] moves` times (default 3, read from the base branch; a key, the person's revision R1), and the question names the number.
- ~~A new trailer for an unreviewed fix, or a field on `Sdlc-Landed`?~~ Resolved: a field, `unreviewed=<n|unknown>`, carried to `Sdlc-Totals`; the retro report line is a later seed. 104 reuses 097's `_amend_record()` with an `also` keyword, and a fix is asked for by a fourth answer, `yes, with a fix` (the person, at the run's question).
