---
id: 129
slug: factory-weighs-nits
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-18-6
depends_on:
serves: [O6]
---

# 129 — The factory weighs its agents' nits and files them as [nit] entries

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Since 114, the factory's code, security and test reviewers write their nits as `- NIT:` lines, and
`carry` records each in `findings.md` as `minor` with `Reason: raised by an agent; not weighed or
filed`. Ship weighs each nit under the process doc's rubric (theme, paths, cost, value),
recommends fixing the cheap and worthwhile ones, and files the rest as `[nit]` entries; the factory
does none of it, so its nits are seen once and lost. 114's notes: "the factory records its agents'
`- NIT:` lines in `findings.md` but never weighs them (theme, cost, value) or files them as `[nit]`
entries, as ship does." It is the `nits` row of `guide/review.md`'s Review dimensions, marked a gap.

## Outcome

- A factory run weighs each agent nit and records it as `fix` (for the builder), `recorded` (a
  proposed `[nit]` entry) or `minor`.
- The landing's question shows the nits it would file, and its yes files them in the register,
  ids from the same `next-entry` call.
- Tests cover the weighing and the filing.
- **Moves O6:** a factory change leaves its small debts where `/sdlc:status` shows them.

## Affected

- **Area:** the factory's review and landing.
- **Files & components:** `plugins/factory/scripts/factory.py` (`carry`, the approve prompt,
  `land_parts()`, `_dispose()`), the approver or reviewer prompts, the land skill, possibly
  `skills/ship/`.
- **Downstream:** the register, `/sdlc:status`, retro.
- **Contracts:** agents that judge have no Write; nothing filed without the person's yes; `[nit]`
  entries keep their shape (`Theme:`, `Paths:`, `Cost:`, `Value:`, `Raised by:`); the cap of 5.

## Constraints

- No agent writes the register, and the factory's review is never counted as the person's.

## Open questions

- ~~Who weighs them: the approver, or the reviewer that raised each?~~ Resolved: the reviewer that raised each, and the script turns the weights into a disposition (spec R1–R2).
- ~~Does a `fix` nit go to the builder in the same run, or only at landing?~~ Resolved: the same run, only inside a rework that runs anyway (spec R3–R4).
- ~~Is a nit a later round no longer raises dropped?~~ Resolved: no; only a handed `fix` nit not raised again is `fixed`, every other is filed (spec R5).
