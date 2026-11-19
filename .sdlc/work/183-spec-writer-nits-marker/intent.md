---
id: 183
slug: spec-writer-nits-marker
tier: 1
impact: patch
stage: shipped
created: 2026-11-19
opened: 2026-11-19T11:03Z
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
fixes: [2026-11-19-50]
serves: [O6]
---

# 183 — The factory's spec-writer writes the Nits taken in: line

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Bug 2026-11-19-50 (low): since 181, a landing retires a nit only when its id is on a
`Nits taken in:` line in the intent's Approach or the spec's Requirements. 181 taught
`skills/intent`, `skills/intent/batch.md`, `skills/spec` and the land skill to write that line, but
not the factory's spec-writer: neither `plugins/factory/agents/spec-writer.md` nor
`plugins/factory/prompts/spec.md` mentions nits at all. Seen on 175: its draft took in nits
2026-11-19-19 and -21 in R13 and R14 by prose only, so its landing would have left both open;
caught by hand and revised with R1. Every factory Tier 2 that takes a nit in has the same gap until
this lands.

## Outcome

- The spec-writer's agent file and the spec prompt say that every nit the spec takes in goes, by
  id, on a `Nits taken in:` line in its Requirements, in the words `skills/spec/SKILL.md` uses,
  and that an id anywhere else retires nothing.
- A test pins it, beside 181's `test_every_place_that_takes_a_nit_in_names_the_marker`, so the
  next place that takes nits in can't miss it.
- **Moves O6:** a factory-built change that takes a nit in retires it without the person catching
  the omission by hand.

## Affected

- **Area:** the factory's spec-writer.
- **Files & components:** `plugins/factory/agents/spec-writer.md`, `plugins/factory/prompts/spec.md`
  (and its built copy under `tests/prompts/` if one is pinned), `tests/test_skills.py` or
  `tests/test_prompts.py`.
- **Downstream:** every factory spec draft from now on; the landing's `named_nits()` reads the line
  unchanged.
- **Contracts:** the marker's form is 181's (`TAKEN_RE`), unchanged; the spec-writer still writes
  no files.

## Constraints

- Wording only: no change to how `factory.py` reads the marker.
- The spec-writer never takes a nit in unasked: only those the intent's Problem or the person
  names.

## Open questions

- ~~Should the spec prompt hand the spec-writer the open nits on the change's paths, as
  `sdlc.py nits --touching` gives the core skill, or only say how to write those the intent names?~~
  Only those the intent names: the Constraints already say it never takes one in unasked, and the
  spec-writer can run nothing (a default in round 1's build report).

## Approach

Add the marker rule to `spec-writer.md` and the spec prompt, worded as `skills/spec/SKILL.md:76-79`
words it. Extend 181's marker test, or add one beside it, to fail if either file stops saying
`Nits taken in:`. Re-record the built spec prompt fixture if `test_prompts.py` pins it.
