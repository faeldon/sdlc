---
id: 047
slug: cut-extra-stops
tier: 2
impact: minor
stage: shipped
created: 2026-11-10
updated: 2026-11-11
shipped: 2026-11-11
idea: 2026-10-26-5
depends_on:
serves: [O3]
---

# 047 — Cut the stops a change makes between its gates

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Every one of the last 14 changes went over O3's stop target, by a median of about 3.5 stops (046:
12 against 6, 044: 17 against 6, 041: 15 against 6). The seed blamed tool permission prompts, but
that count was mislabelled: 042 fixed it, and since then every `Close` commit records `prompts=0
prompt_modes=auto`. No tool has stopped the person here.

Most of the excess is `extra` stops: a message the person typed between gates that wasn't a slash
command (`metrics.py`'s `kind: "extra"`). Over those 14 changes there were 24 in ship, 14 in
design, 6 in intent and 6 in build, beside the questions (`AskUserQuestion`: 15 in intent, 9 in
design). Nothing yet says what each extra stop was. It could be the agent asking in prose instead
of at the gate, a revision of a draft, the person nudging a stopped turn to carry on, a ship that
stops on findings and needs "fix it", or a harness turn read as typed (the docstring's "Tool
loaded." caveat). So there is nothing to target yet.

## Outcome

- Close records why each extra stop happened, as a class (numbers and names only, per the metrics
  contract), as a new field or trailer beside the existing ones, so `retro` can say which kinds
  recur.
- The avoidable kinds found in this repo's transcripts are cut where they start: a skill that asks
  in prose what its WAIT could ask, a ship that stops before its one question, a harness turn
  counted as the person's.
- **Moves O3:** the median change's stops above target fall from about 3.5 toward 1.5, ship's extra
  stops, the largest share, first.

## Affected

- **Area:** the skills' conversation between gates, mostly ship and spec; close's `measure` step.
- **Files & components:** `skills/ship/SKILL.md`, `skills/spec/SKILL.md`,
  `skills/intent/SKILL.md`; `scripts/metrics.py` (`read_events`, `summarize`, `trailers`,
  `parse_trailers`); `scripts/sdlc.py` (retro's metrics); `tests/test_metrics.py`;
  `docs/REFERENCE.md` (*Metrics*).
- **Downstream:** every host's sessions through the skills it runs; every host's `Close` commits
  and retrospectives; the factory's eval and review, which read `Sdlc-*` trailers through pinned
  copies of the parsing.
- **Contracts:** the metrics event list and trailer format (extend, never redefine); no message
  text leaves `read_events`; measuring never refuses; each skill keeps exactly one WAIT.

## Constraints

- **A WAIT keeps its meaning.** Cutting stops never cuts a gate or folds one approval into another;
  what a WAIT approves is always Tier 2 here.
- **No message text.** A stop's class comes from its shape (it follows a question in prose, it
  follows a refused turn, it is a short "yes"), never from storing what was said.
- **Old trailers still parse.** A `Close` commit without the new field reads as "not classified",
  never as zero.
- **Mechanism, not this repo's habits.** A cut has to help any host, not just the way this repo's
  person works.

## Open questions

- ~~Which classes of extra stop can be told apart from a transcript's shape alone, without reading
  message text?~~ Resolved: all of them: harness by its entry's keys, commands and interrupts by
  their prefix, after-gate and revise by their place in a span, asked by the agent's trailing `?`
  (spec R3).
- ~~How many of the extra stops are harness turns (a "Tool loaded." entry), not the person at all?
  Those are a measurement fix, not a skill fix.~~ Resolved: 15 of 53 over 14 changes, task notices
  and compaction summaries; "Tool loaded." never lands as a user entry (spec R1).
- ~~Is a revision of a draft before its WAIT (an "edit a section" answer given in prose) a stop worth
  cutting, or the gate doing its job?~~ Resolved: the gate doing its job; counted, as `revise`.
- ~~Should ship's "fix the finding first" round trip count against the target at all, or be measured
  apart, as spikes are from rework?~~ Resolved: it counts, as `revise`; folding it away would join
  two approvals.
- ~~Does the seed's original aim, covering tool prompts for hosts in default mode, still need its own
  seed once this lands?~~ Resolved: yes; ship carries it forward as a seed of its own.
