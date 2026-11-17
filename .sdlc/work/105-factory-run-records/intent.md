---
id: 105
slug: factory-run-records
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-42, 2026-11-17-44, 2026-11-17-48]
depends_on:
serves: [O6]
---

# 105 — A factory run's records say what it did

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Three places a factory run's records mislead or get cut:

- **2026-11-17-42:** "`factory.py agent --task spec` returns the draft only in its reply, so the supervisor cuts `spec.md` out of the text; a draft holding its own code fences was cut short twice on 2026-11-17."
- **2026-11-17-44:** "086's D2 (no badge on a shipped escalated card) and D4 (keep `was ESCALATE`) contradicted each other, and only the approver noticed."
- **2026-11-17-48:** "`check --strict` reports 'plan.md is still the template at stage: build' for a factory change whose builder is writing that plan right now."

## Outcome

- The spec-writer's draft is written whole to the change's folder (`runs/spec-draft.md`), and the build and spec skills copy it into `spec.md` after the yes; a draft with fenced code survives; a test.
- `factory.py decisions` asks of a new default whether it replaces an earlier one and marks the earlier `superseded` in `decisions.md`; the approver and ship read the ledger without the contradiction; a test.
- `check --strict` leaves out the template-plan problem for a change whose `runs/step.md` names a live first build; a test.
- **Moves O6:** a run's records say what the run did.

## Affected

- **Area:** sdlc-factory's agent, decisions and the audit.
- **Files & components:** `plugins/factory/scripts/factory.py` (`agent --task spec`, `decisions`), `plugins/factory/skills/build/SKILL.md` and `spec/SKILL.md`, `plugins/factory/agents/spec-writer.md`, `scripts/sdlc.py` (`check`), `scripts/board.py` if it reads `decisions.md`, tests.
- **Downstream:** every factory spec draft and decision ledger; `check --strict` in every gate.
- **Contracts:** agents that judge have no Write (the script writes the draft, not the agent); `sdlc` reads a run's files with copies of `factory.py`'s parsing, pinned by tests; the decisions ledger's shape is read by ship and the board.

## Constraints

- No agent gains Write.
- `check --strict` stays a gate: only that one problem, only while a run is live.

## Open questions

- ~~Who decides a default supersedes another: the agent raising it, or `decisions` by matching what they're about?~~ Resolved: the agent, by `(supersedes D<n>)` on its `[default]` line; `decisions` only records and checks it (spec R5, R6). The person kept the 3-hour liveness window, the draft files after `write-spec`, and the spec skill's switch to `factory.py agent`, at the run's question.
