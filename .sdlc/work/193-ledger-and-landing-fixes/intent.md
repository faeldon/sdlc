---
id: 193
slug: ledger-and-landing-fixes
tier: 1
impact: patch
stage: shipped
created: 2026-11-20
opened: 2026-11-19T23:49Z
updated: 2026-11-20
shipped: 2026-11-20
idea: 2026-11-19-68
depends_on:
fixes: [2026-11-19-79]
serves: [O6]
---

# 193 — The decisions ledger keeps whole questions, and the landing's loose ends are tidied

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Bug 2026-11-19-79: when an agent's `- DECISION:` line continues its question in sub-bullets,
`sub_lines()` stops at the first one, so `decisions.md` keeps only the first line and the options
are lost. 187's D3 reached `/sdlc-factory:decide` as "I reworded more than R7 and R9 list:" with no
options. Related: 187's builder raised the same decision twice (D1/D4, D2/D5; nit 2026-11-20-1).

Idea 2026-11-19-68: the land skill's description doesn't name the build at the tip or the
approver's judgement of changed checks. And 185 left four nits in `landing.py` and AGENTS.md:

- 2026-11-19-74 (security): `--der` passes the `--dereference-recursive` refusal, because GNU grep
  accepts long-option prefixes;
- 2026-11-19-71 and -72: docstrings;
- 2026-11-19-70: two AGENTS.md lines past the wrap.

## Outcome

- A decision's question keeps every line, and its options and why are read under it.
- A decision raised twice in one reply lands once.
- The land skill's description says what a landing runs.
- The read-only list refuses any prefix of grep's symlink-following long options.
- **Moves O6:** the person decides from the whole question, and the unattended landing's allow-list
  has one less gap.

## Affected

- `plugins/factory/scripts/factory.py` (`sub_lines`, `raised_decisions`),
  `plugins/factory/scripts/landing.py` (sensitive), `plugins/factory/skills/land/SKILL.md`,
  AGENTS.md, `tests/test_factory.py`, `tests/test_train.py`.
- **What reads it:** `/sdlc-factory:decide`, `/sdlc:ship` and the board.

## Constraints

- Ledgers already written still read.
- The read-only list only gets stricter.
- `factory_records.py`'s pinned copies stay in step.

## Approach

Let `sub_lines()` collect a question's continuation lines before the `- OPTION:` and `- WHY:` run,
and fold them into the question. Dedupe identical decisions in `raised_decisions()`. Refuse any long
option of three or more characters that is a prefix of `--dereference-recursive`. Fix the
docstrings, the wrap and the description.

Nits taken in: 2026-11-20-1, 2026-11-19-74, 2026-11-19-71, 2026-11-19-72, 2026-11-19-70

## Open questions

None.
