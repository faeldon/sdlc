---
id: 142
slug: pay-down-todays-nits
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: [2026-11-18-25, 2026-11-18-28, 2026-11-18-29, 2026-11-18-30, 2026-11-18-31, 2026-11-18-34, 2026-11-18-35, 2026-11-18-36, 2026-11-18-37]
depends_on:
serves: none
---

# 142 — Pay down the nits today's landings left

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

134, 136 and 138's reviews filed nine `[nit]` entries, all cost S, all in files the release
ships:

- Wraps: `AGENTS.md:118-119` and around `:166` (2026-11-18-25); `skills/triage/SKILL.md:58` at
  168 characters (2026-11-18-29).
- A stray `# fmt: skip` at `scripts/sdlc.py:7620` (2026-11-18-28).
- Docstrings at `tests/test_board.py:1886-1915` citing "138 C1"/"C2", which no reader can resolve
  (2026-11-18-30).
- `test_no_build_question_for_a_refusal_or_a_spec`, whose name no longer fits (2026-11-18-31).
- `plugins/factory/skills/build/SKILL.md:416` describing `exhausted` without `stuck` or
  `untestable` (2026-11-18-34).
- `reviewer-ux.md`'s re-raise sentence, which may not match the other reviewers'
  (2026-11-18-35).
- R6's README table, which can't be tested mechanically (2026-11-18-36), and R3 with no
  `verified.md` (2026-11-18-37).

## Outcome

- Every nit above is fixed, or retired with its reason; `/sdlc:status` lists none of them after
  ship, and `./check.sh` passes.

## Affected

`AGENTS.md`, `scripts/sdlc.py`, `skills/triage/SKILL.md`, `tests/test_board.py`,
`tests/test_factory.py`, `plugins/factory/skills/build/SKILL.md` and
`plugins/factory/agents/reviewer-ux.md`. Nothing reads them but people and the tests.

## Constraints

- No behaviour changes.
- The skills' line budgets and wraps hold; `AGENTS.md` stays the map, reflowed only.

## Open questions

- None.

## Approach

Reflow 2026-11-18-25 and 2026-11-18-29 at the files' ~100 columns. Remove 2026-11-18-28's
`# fmt: skip` if `ruff format --check` agrees. Replace 2026-11-18-30's "138 C1/C2" with the rule
each test pins. Rename 2026-11-18-31's test to say a Tier 1 spec. Add 2026-11-18-34's clause that
the approver is told which stop it was. Make 2026-11-18-35's sentence match the other five
reviewers' word for word. Add 2026-11-18-37's one-line fixture. Retire 2026-11-18-36 as not
testable, with a comment at `tests/test_factory.py:1676` that the table is checked by hand against
each `Close` commit.
