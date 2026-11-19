---
id: 166
slug: untestable-none-and-waits
tier: 1
impact: patch
stage: shipped
created: 2026-11-19
opened: 2026-11-19T01:17Z
updated: 2026-11-19
shipped: 2026-11-19
idea: 2026-11-18-91
depends_on:
fixes: [2026-11-18-95]
serves: [O6]
---

# 166 — A builder's "none" isn't an untestable requirement, and agents wait without sleep

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two things make a factory run spend turns or stop for nothing. A builder that writes
`- UNTESTABLE: none.` is read as having one untestable requirement named "none.": `UNTESTABLE_RE`
(`plugins/factory/scripts/factory.py:275`, and core's pinned copy at `scripts/factory_records.py:90`)
captures any text, so `early_stop()` stops the run and the approver must ESCALATE a change with no
gap. 155's round 1 showed it: three PASSes, a green gate, and an ESCALATE whose only reasons were
this stop and a look (bug 2026-11-18-95, introduced by 136-factory-rounds-that-catch-enough). And
the 2026-11-18 retrospective counted `Bash:sleep` failing 18 of the 19 times it was called (error
share 0.95), across 12 of the 41 changes that recorded tool calls: the harness refuses a foreground
sleep, so every call is a spent turn, and the agents that wait on something (the builder and the
behaviour reviewer, most likely) are never told how to wait instead (idea 2026-11-18-91).

## Outcome

- `- UNTESTABLE: none`, `none.`, `None`, `n/a` (any case, with or without a period) count as no
  untestable requirement: `verdicts` doesn't stop on them, and the builder report's untestable list
  is empty. A test fails if any of those stops a run, or if a real one
  (`- UNTESTABLE: R3 needs a live GitHub`) stops being one.
- The change is made in `factory.py` and `factory_records.py`'s pinned copy together, so the
  name-wide pin test still passes, and the board and `status` read the same.
- The builder's and the behaviour reviewer's instructions say how to wait without `sleep`: run the
  command with its own timeout, or poll with a bounded loop in one command. Each prompt or agent
  file that changes says so in plain words. The next retrospective's `Bash:sleep` count is how this
  is judged; nothing in this change measures it.
- **Moves O6:** a run stops its person only for a real gap, never for a builder writing "none".

## Affected

- **Area:** the factory's reading of builder reports, and its agents' instructions.
- **Files & components:** `plugins/factory/scripts/factory.py` (`UNTESTABLE_RE` or where its
  matches are read), `scripts/factory_records.py` (its copy), `plugins/factory/prompts/*.md` and/or
  `plugins/factory/agents/builder.md` and `reviewer-behaviour.md`, tests in `tests/test_factory.py`,
  `tests/test_modules.py` and `tests/test_prompts.py`.
- **Downstream:** every factory run, here and in hosts with the factory; the board and `status`
  read untestable lines through the copy.
- **Contracts:** core reads the factory's records only through `factory_records.py`, its copies
  pinned by name (163), so both change together; prompt files are read only from the plugin and
  their parts checked against what the script fills (164), so a changed part's placeholders change
  `PROMPT_PARTS` too.

## Constraints

- A real untestable requirement still stops the run; only the empty answers stop counting.
- The prompts' recorded copies (`tests/prompts/*.txt`) change only where the wording does,
  re-recorded deliberately.

## Open questions

- Filter "none" where the lines are read, or make the regex refuse it (which changes a pinned
  constant in both places).
- Whether the wait guidance belongs in the shared `common.md` or only in the build and review
  prompts.

## Approach

Make the reader of `- UNTESTABLE:` lines drop empty answers (`^(none|n/?a)\.?$`, case-insensitive)
in `factory.py` and `factory_records.py` alike, with tests for each spelling and for a real one.
Add a short "waiting" paragraph to the builder's and the behaviour reviewer's instructions: never
`sleep`; give the command a timeout, or poll in one bounded command. Re-record the affected prompt
copies. The four nits open on `factory.py` (2026-11-18-68, -69, -80, -84) are left to R3, as the
scorecard's waves plan; none is taken in here.
