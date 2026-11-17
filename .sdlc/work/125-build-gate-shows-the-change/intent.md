---
id: 125
slug: build-gate-shows-the-change
tier: 1
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O6]
---

# 125 — The factory's build gate shows what the change is for, in a question the script words

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The person approves a factory run at `/sdlc-factory:build`'s Step 2, and Step 1
(`plugins/factory/skills/build/SKILL.md`) lists only the run's machinery to show first: the tier,
`fresh`'s rebase, the gate command, every agent and its model at both depths, round limits, the
depth rule, the mode, the `[ui]` server, `max_runs` and the files it writes. Nothing tells the
supervisor to show what the change is for. A Tier 2 at least shows the spec draft; a Tier 1 has
none, so the yes is given on machinery alone. On 2026-11-18, 124-board-renders-markdown was
approved from a screen naming haiku and opus, `serve.sh` and 32 runs, and not one line of its
Problem or Outcome.

The question is also worded by hand: the skill gives three template sentences (spec draft, none,
restart) with placeholders the supervisor model fills from `start`'s JSON. Landing's question comes
from `factory.py land-check` (`land_question()`) and ship's from `sdlc.py preflight --question`, so
the build gate is the one factory WAIT a model words for itself, with nothing checking the sentence
matches the template.

## Outcome

- Step 1 opens with the change itself, quoted from its folder, never summarised: its title, its
  Problem and Outcome from `intent.md`, and its Approach for a Tier 1 (for a restart, the intent's
  title too, before the approver's reasons). The machinery follows, as now.
- `factory.py start` prints `question`: the build question worded by the script, in its three
  forms, with the `[review] sensitive` parenthesis, the no-gate clause and the `[ui]` clause taken
  from what `start` already reads, as `land-check` does.
- The skill's Step 2 asks `start`'s `question` literally, as `land` asks `land-check`'s, and the
  three template sentences leave the skill.
- A test builds `start` on fixtures (with and without sensitive paths, a gate and `[ui]`; a spec
  draft; a restart) and pins each form and each clause.
- **Moves O6:** a person approving a factory run sees what it will build before what it will cost,
  so a run is approved for its purpose, not waved through on its machinery.

## Affected

- **Area:** the factory's build skill and `factory.py`.
- **Files & components:** `plugins/factory/skills/build/SKILL.md` (Steps 1–2);
  `plugins/factory/scripts/factory.py` (`cmd_start`, a new `build_question()`);
  `tests/test_factory.py`; the factory README if it quotes the question.
- **Downstream:** the person at the build gate, and every supervisor session running the skill. A
  `question` field in `start`'s JSON is additive. `/sdlc-factory:spec` has its own WAIT and is out
  of scope unless the plan finds it shares the problem.
- **Contracts:** every WAIT asks its literal question in an `AskUserQuestion` dialog
  (`test_every_wait_asks_in_a_dialog`); "a skill's WAIT step: what it approves, or when" is always
  Tier 2, and here what the yes approves stays the same, only who words it and what's shown beside
  it changes; `factory.py` never imports `sdlc.py`.

## Constraints

- What the yes approves is unchanged: the same sentences, word for word as the skill holds them
  today, now printed by the script.
- `start` stays read-only. Step 1 quotes the intent, never paraphrases it.

## Open questions

- How much of a long intent to show: all of Problem and Outcome, or up to a length with a pointer
  to the file?
- Do the restart and spec-draft forms show the intent too, or just its title, since the spec or
  the approver's reasons already say what it's for?
- Does `/sdlc-factory:spec`'s WAIT have the same hand-worded question, and should it move to the
  script in this change?

## Approach

`build_question(cfg, start, spec, restart)` in `factory.py`, worded from today's three template
sentences, and `start`'s JSON gains `question` from it. Step 1 is edited to lead with the intent's
title, Problem, Outcome and (Tier 1) Approach, quoted, and Step 2 to ask `start`'s `question`
literally. Tests in `tests/test_factory.py` for each form and clause. No open nits touch these
paths.
