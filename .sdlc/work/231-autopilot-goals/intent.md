---
id: 231
slug: autopilot-goals
tier: 2
impact: minor
stage: shipped
created: 2026-11-22
opened: 2026-11-22T01:57Z
updated: 2026-11-22
shipped: 2026-11-22
idea: 2026-11-22-19
depends_on:
serves: [O6]
origin: self
---

# 231 — Autopilot runs toward a goal, and plans the seeds it takes to reach it

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Autopilot (216) picks its work by rank, not by purpose. `autopilot --preview` lists the register's
ready seeds "in rank order (bugs by severity, `Priority: high`, the product doc's outcomes)", and
the planner (`plugins/factory/agents/autopilot-planner.md`) returns a `- WAVE:` list from them.
Nothing tells a run what it is for, so nothing can say whether a seed moves it closer.

From 2026-11-22-19, in the person's words: "Autopilot plans the seeds it takes: groups them by the
risk they lower for the next goal, checks each against the code before drafting (dropping ones
already fixed or wrong), tiers and orders them by shared files, says what waits and why, and flags
a backlog growing faster than it drains — as the supervisor planned 1.12 on 2026-11-22."

And from the person, on what that needs first: "one of the input that autopilot would require
would be some guidance around what are the goals for the autopilot run. I'm thinking if none is
provided, then it can work out based on the current milestones and goals that were identified
during the last retrospective. It can also provide suggestions based on what the current
outstanding seeds look like and which one could be a potential goal for churning the seeds. Or it
could be a stated goal by the human."

The goals are already written down: `.sdlc/DIRECTION.md` holds the last retrospective's goals
(G7–G9) and milestones (M13–M23), and autopilot reads neither.

## Outcome

- An autopilot run has one goal, fixed at `--begin`, from one of three sources:
  - **stated** by the person in the bounds;
  - **from the direction doc**, a goal or milestone the last retrospective set, when none is stated;
  - **suggested from the register**, a goal the open seeds point at (a theme or cluster worth
    clearing), offered beside the direction doc's.
- The bounds step shows the goal and where it came from, and the WAIT's question and `shown` name
  it, so the yes approves the goal along with the caps.
- The planner is given the goal and plans toward it, as 2026-11-22-19 says:
  - groups the candidates by the risk they lower for the goal;
  - checks each against the code before an intent is drafted, and leaves out one already fixed or
    wrong, saying why;
  - tiers and orders what it takes by the files they share;
  - says what waits, and why.
- The run's report says whether the register grew faster than the run drained it.
- **Moves O6:** an unattended run spends its budget on what the person or the last retrospective
  said matters, and says what it left and why.

## Affected

- **Area:** the factory's autopilot: its bounds, its WAIT, its planner, its report.
- **Files & components:** `plugins/factory/skills/autopilot/SKILL.md` (Step 1's bounds, the WAIT),
  `plugins/factory/scripts/autopilot.py` (`--preview`, `--begin`, the state, the wave brief, the
  report), `plugins/factory/agents/autopilot-planner.md`, the direction doc's reader, the factory
  README, and their tests.
- **Downstream:** every host that runs `/sdlc-factory:autopilot`; a host with no direction doc still
  has the stated and suggested goals.
- **Contracts:** a skill's WAIT (autopilot's single yes now also approves a goal); autopilot's
  bounds are fixed at `--begin`; agents that judge have no Write (the planner reads the code, it
  doesn't run checks or edit); `autopilot.py` is `[review] sensitive`; the direction doc is the
  retrospective's, and autopilot only reads it.

## Constraints

- The goal narrows what autopilot takes; it never widens the bounds, the guards or `hold_causes()`.
- A seed the planner calls already fixed or wrong is left for the person, never retired by the run.
- Autopilot never writes the direction doc or the register.

## Open questions

- ~~With no goal stated, does the run take the direction doc's top goal unasked, or must the person
  pick one of the proposed ones at the WAIT?~~ Resolved: neither unasked; the preview proposes one
  and the WAIT names it, so the yes approves it (spec R4–R6).
- ~~How is a goal "suggested from the register" found: by the script (themes, counts, age) or by
  the planner reading the seeds?~~ Resolved: by the script, from the candidates' themes and counts
  (spec R4).
- ~~What does the planner's reply become: the `- WAVE:` list plus a reason per seed and a `- WAITS:`
  list, or a plan file of its own the report shows?~~ Resolved: grouped WAVE, WAITS and LEAVE lines
  the script checks, shown in the summary (spec R8, R11).
- ~~How does "checks each against the code" stay inside the planner's Read/Grep/Glob, and what does
  the run do with a seed it calls wrong: hold it, skip it, or file nothing?~~ Resolved: the planner
  reads, the script checks a cited path exists, and the seed is left for the person (spec R8, R9).
- ~~Is "the backlog grew faster than it drained" a count over the run (filed against taken) or
  against the last retrospective's register size?~~ Resolved: over the run, filed against drained
  (spec R11).
