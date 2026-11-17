---
id: 121
slug: landing-review-base
tier: 1
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
fixes: [2026-11-17-86]
serves: [O3, O6]
---

# 121 — A landing review reads its change from the round's own base

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-86:** a landing review compares a rebased change against the base branch as it is
now, not against the commit the change was rebased onto. So a commit that reaches the base branch
during the landing reads as something the change deleted. On 2026-11-17, 110-board-says-it-plainly's
landing round 1 was rebased onto 09a8622; bug 2026-11-17-85 was then filed on main (e7e2f1a); the
landing's code reviewer reported that the branch "drops" 85 from `.sdlc/work/inbox.md`, the
verifier kept it, and `land-verdicts` stopped the landing ("the landing review kept 1 change(s):
ship it by hand"). The branch never held 85. The same happened to 116's landing an hour later,
when 111 closed under it. Both times the person had to run the landing again by hand.

## Outcome

- A landing review reads the change's diff from the commit its round was rebased onto (the round's
  gated head's merge base), so a commit that reached the base branch since is never reported as
  the change's.
- A landing round whose base has moved since is caught by the script, as `moved` at close already
  is, never by a reviewer's finding.
- A test in `tests/test_land.py` rebases a change, adds a commit to the base branch, and checks the
  landing review's prompt names the round's base, not the moved one.
- **Moves O3:** a landing stops only for what needs the person.
- **Moves O6:** the factory finishes a landing without a hand step when the base moves.

## Affected

- **Area:** sdlc-factory's landing review.
- **Files & components:** `plugins/factory/scripts/factory.py` (the `land-review` and
  `land-verify` prompts, and the diff they name), `plugins/factory/agents/reviewer-code.md` and the
  other reviewers' landing wording, `tests/test_land.py`.
- **Downstream:** every factory landing.
- **Overlaps:** 112, 113 and 119, now building, also edit `factory.py`; build this after at least
  one of them lands.
- **Contracts:** a reviewer's reply is never patched; landing commits only through sdlc's own
  steps.

## Constraints

- A base that really moved still sends the change back through a landing round: only the false
  finding goes.

## Approach

Record the base each landing round was rebased onto (its gate already records the head), and pass
`git diff <that base>...HEAD` to the landing's reviewers and verifier in place of the diff against
the base branch's tip. Tell them in the prompt that the base branch may have moved since, and that
the script handles that. Pin it with the test above.

## Open questions

- Is the round's base best read from the gate record, or recorded by `land` when it rebases?
