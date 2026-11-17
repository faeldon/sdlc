---
id: 106
slug: factory-reviewer-coverage
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: [2026-11-17-45, 2026-11-17-46]
depends_on:
serves: [O6]
---

# 106 — Factory review reads the tests and sees the new cards

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two review blind spots in the factory:

- **2026-11-17-45:** "At the light depth only the code reviewer runs, so 092's and 095's tests were never read requirement by requirement, and both approvers said so."
- **2026-11-17-46:** "No screenshot on 2026-11-17 showed 088's step track, 086's `was ESCALATE` or 091's gate badge: the dev server served this repo's board, whose changes had none of those states, so the ui and ux reviewers judged them from code alone."

## Outcome

- A Tier 2 change's light rounds include the test reviewer (the default `factory.light` for a Tier 2), and `verdicts` lists it in `missing`; a test.
- `[ui]` can name fixture data the dev server starts with (a key whose default is none), and this repo's config names a fixture with a change in each state its board shows; the shots show the cards a change adds; a test.
- **Moves O6:** a factory review reads what a change's tests prove and what its page shows.

## Affected

- **Area:** sdlc-factory's depth and UI review.
- **Files & components:** `plugins/factory/scripts/factory.py` (depth, `verdicts`, `agent`'s server start), `.sdlc/factory.toml` and `[ui]` in `.sdlc/config.toml`, `plugins/factory/README.md`, `docs/REFERENCE.md` (`[ui]`), `tests/test_factory.py`, a fixture under `tests/fixtures/` or `evals/fixtures/`.
- **Downstream:** every factory run's cost at the light depth (one more reviewer per Tier 2 round); hosts with `[ui]`.
- **Contracts:** a new config key whose default keeps today's behaviour; the depth rule (a run never lightens).

## Constraints

- A Tier 1 at the light depth keeps today's reviewers.
- A fixture is data only: the server serves it, the review writes nothing.

## Open questions

- ~~The test reviewer at light depth by default for Tier 2, or a `factory.light_tier2` setting?~~ Resolved: by default, no new setting; a host's own `[light] reviewers` is kept at both tiers (spec R1–R5). The person accepted the default's cost and that a run straddling the upgrade is asked for a test review, at the run's question.
- ~~What shape is the fixture: a scratch repo the server is pointed at, or files a `serve` command reads?~~ Resolved: both, in layers: the plugin copies `[ui] fixture` and passes it as `{fixture}`; this repo's `serve` builds a scratch git repo from it (spec R9–R13).
