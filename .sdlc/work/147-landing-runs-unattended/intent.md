---
id: 147
slug: landing-runs-unattended
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-44, 2026-11-18-45, 2026-11-18-46]
depends_on: [139]
serves: [O6]
---

# 147 — A landing runs unattended after its one yes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc-factory:land` takes a Claude session for the whole landing. After the person's one yes,
the session does nothing that needs judgement: it runs the next step the script names, waits,
reads the result, and runs the next. With 139, `factory.py train` names every step (commit,
stack, gate, bisect, eject, review, close). A train of four changes, with gates, landing reviews
and possible bisection, can run for an hour. Meanwhile that session can't supervise builds, so
the advice is to run landing "from a session of its own": the person keeps two sessions open,
and one of them is an LLM spending tokens to sequence commands a loop could run.

## Outcome

- After the landing's yes, `factory.py train --run` executes the steps `train` names, in order,
  and starts the judging agents itself (the train's resolver, the landing reviewers, the
  verifier, mends), as `factory.py agent` already does. It writes each step to
  `runs/land-step.md` for the board as it goes.
- It exits at the first stop that needs the person (a red gate it can't bisect, a kept change, a
  used-up mend, an ejection, a move past `land.moves`, a refused push), naming the stop and the
  way on. Rerunning `train --run` resumes from the train's saved state.
- The question, the paid skills' cases and the acceptance checks run in the session before the
  loop starts, each behind its prompt; the loop runs nothing that needs one.
- Only the script commits or pushes, as now: the loop is the script, not an agent.
- A test runs `train --run` on a batch of three in a scratch repo with stand-in agents and finds
  them landed, each step recorded; another stops it at a kept change and finds the stop named and
  the rest not landed.
- **Moves O6:** a landing stops the person only where it needs them, and doesn't occupy a session
  while it runs.

## Affected

`plugins/factory/scripts/factory.py` (a `train --run` loop over 139's steps),
`plugins/factory/skills/land/SKILL.md` (the question, cases and checks, then the loop in the
background), the board (which already reads `runs/land-step.md`), `plugins/factory/README.md` and
`docs/REFERENCE.md`. Every factory host's landing. It waits on 139, whose `train` it runs.

## Constraints

- Only the script commits or pushes; no agent orchestrates or writes history.
- Nothing runs unasked: the yes, the paid cases and the acceptance checks stay behind their
  prompts, before the loop.
- Every stop is the person's: the loop never decides past one, and never retries a stop itself
  beyond the mends already allowed.
- One landing at a time (139's R19): a second `train --run` refuses while one runs.
- A crash or a kill leaves state that resumes, never a half-landed change (139's R11 and R12 hold).

## Open questions

- ~~Build it after the first train landing (140–143, by hand), so the stops it handles are the ones
  that run shows?~~ Resolved: agreed 2026-11-18.
- ~~How does the person cancel a running loop, and what does a cancel leave?~~ Resolved:
  `train --cancel`, checked between steps; killing the task is the hard stop (spec R7, R8).
- ~~Does the loop notify the person when it stops (a push notification, a status line), or does the
  board alone show it?~~ Resolved: the harness's background-task notice and the board (spec R11).
- ~~How does the land skill start it in the background and still report its result, without the
  session waiting on it?~~ Resolved: `run_in_background`, reported when it exits (spec R11).
