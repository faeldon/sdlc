---
id: 131
slug: land-gate-shows-the-change
tier: 1
impact: patch
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on:
serves: [O6]
---

# 131 — The landing's gate shows what each change is and what its yes files, inside the dialog

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

In the person's words: when landing an escalated change, the question reads "Land 1 change in this
order, 124-board-renders-markdown, each shipped with its approver's impact, its undone notes
carried, filed as bugs or dropped and its assumed decisions confirmed as shown, …" — "I would like
to see what the undone notes that will be carried or filed as bugged or dropped before I approve. I
also like to have the same details as in 125 what the change is as a summary."

The question says "as shown", but what it refers to (each undone note's disposition, which for 124
was one seed, one bug and one drop, and each assumed decision) lives only in text the supervisor
printed above the dialog, which the dialog can push out of view. And nowhere, in the dialog or
above it, does `/sdlc-factory:land` say what each change *is*: Step 1 lists decision, impact,
overlaps and signals, never the intent's title, Problem or Outcome. So a landing (commit, close,
push) is approved from machinery and dispositions without a line on what the change does.

## Outcome

- Land's Step 1 opens each change with its intent, quoted, not summarised: title, Problem and
  Outcome, as 125 does for the build gate; signals, dispositions, assumed decisions and recovery
  follow.
- `land-check` gives each change in `batch` an `intent` part (title, Problem, Outcome) read from
  its folder, so the skill quotes the script's text instead of reading files itself.
- What the yes approves is visible inside the dialog itself, not only above it: for each change,
  every undone note with its disposition (`→ seed: <title>`, `→ bug, <severity>: <title>
  (<paths>)`, `→ dropped: <reason>`) and every assumed decision by id with what was assumed.
- A test on a fixture batch with a seed, a bug, a drop and an assumed decision pins each change's
  `intent` in `land-check` and each disposition in the text the dialog shows.
- **Moves O6:** a landing is approved knowing what each change does and what will be filed, not
  on "as shown".

## Affected

- **Area:** the factory's landing gate.
- **Files & components:** `plugins/factory/skills/land/SKILL.md` (Steps 1–2);
  `plugins/factory/scripts/factory.py` (`land_parts()` or `land-check`, an intent reader);
  `tests/test_land.py`, possibly `tests/test_skills.py`.
- **Downstream:** the person at every landing; every session running the land skill.
- **Contracts:** `land-check`'s `question` stays the script's and is asked literally
  (`test_every_wait_asks_in_a_dialog`); "a skill's WAIT step: what it approves, or when" is always
  Tier 2, and here the yes approves exactly what it does today, only shown; `factory.py` never
  imports `sdlc.py`.

## Constraints

- The question's wording and what a yes approves don't change.
- The intent is quoted, never paraphrased; `land-check` stays read-only.

## Open questions

- How the detail reaches the dialog: the `yes` option's `preview`, the question's own text, or a
  short block the dialog shows above the options?
- Share 125's intent reader once 125 lands, instead of a second one (and then `depends_on: [125]`)?
- How much of a long intent goes in the dialog, against above it (the same question 125 had)?
- In a batch of five, does each change show its whole intent, or its title only with the full
  text a step up?

## Approach

`land-check` adds `intent` (title, Problem, Outcome) to each batch entry, reusing 125's reader if
it has landed. Land's Step 1 leads each change with it; Step 2 asks the script's `question`
literally, with the batch's dispositions and assumed decisions shown inside the dialog (a
`preview` on `yes` if the plan finds it renders well, else the script's own rendered block).
Tests in `tests/test_land.py`.
