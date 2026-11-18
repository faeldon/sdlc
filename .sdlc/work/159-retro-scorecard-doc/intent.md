---
id: 159
slug: retro-scorecard-doc
tier: 1
impact: none
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O4]
---

# The retrospective's scorecard, written down

## Problem

On 2026-11-18 the retrospective's analysis was worked out by hand, in conversation: where a
change's time goes (opening to landing split into queue, agents working, idle, ready-waiting and
landing), factory against by hand, function-level refactor candidates, and then a framework to
hold it all: a Value band, five pillars (Speed, Quality, Autonomy, Cost, Simplicity), each with a
headline and a guardrail, and a Trust band. It names 16 seeds (S1–S16) and six refactors
(R1–R6) to build it. None of it is written down in the repo. Each seed would have to restate its
metric, and the changes that build them would have no shared reference for what each number
means or why.

## Outcome

- `docs/RETRO-SCORECARD.md` exists. It holds the framework: why it exists, how the scorecard
  reads, the Value band, each pillar's headline, supporting metrics, guardrail and diagnostics,
  the Trust band, the synthesis questions, and the seeds S1–S16 and R1–R6 in a suggested order.
- Every metric in it is explained the same way: what it is, why it matters, where its data comes
  from, and its status (captured, partly, or the seed that adds it).
- `docs/CONTRIBUTING.md`'s layout lists the doc, so a contributor finds it.
- `./check.sh` passes, `test_nothing_local` included: the doc cites no machine path or host.
- **Moves O4:** the next retrospective's analysis changes build to one framework, so its findings
  cite pillars and metrics with a written meaning, not numbers chosen run by run.

## Affected

`docs/RETRO-SCORECARD.md` (new) and a line in `docs/CONTRIBUTING.md`. Nothing reads the doc
mechanically: it is a reference for people and for the agents building S1–S16 and R1–R6. Nothing
a host receives changes, since `docs/` isn't copied into a host.

## Constraints

- It describes and proposes. It changes no rule the code holds, so where it says a figure is
  captured, that has to be true of the code today.
- No machine paths, host names or bare change-folder citations (`test_nothing_local`).

## Open questions

- Whether the framework later moves into `guide/`, so hosts' retrospectives use it too, once
  S14 and S15 build it. Left for those changes.

## Approach

The approved draft is `draft.md` in this change's folder, written with the person on 2026-11-18.
Add it as `docs/RETRO-SCORECARD.md`, keeping its structure and wording. Check each "captured"
status against the code (`scripts/retro.py`, `scripts/metrics.py`, `sdlc.py retro`'s output), and
correct any that overstate, saying which in `notes.md`. Add one line for it to
`docs/CONTRIBUTING.md`'s layout. Run `./check.sh`.
