---
id: 181
slug: landing-nits-and-fixes
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T08:06Z
updated: 2026-11-19
shipped: 2026-11-19
idea:
depends_on:
fixes: [2026-11-19-12, 2026-11-19-30]
serves: [O2, O3]
---

# 181 — A landing retires only the nits it takes in, and goes on past a fix already made

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Two landing bugs, each of which cost a stop on 2026-11-19, both in the factory's landing code.

2026-11-19-12 (med): "A landing retires every nit its intent's Approach or spec's Requirements
names by id, even one named to say it isn't taken: named_nits() (plugins/factory/scripts/factory.py,
NIT_SECTIONS) matches any whole id in those sections. 165's Approach listed its wave plan and
retired 2026-11-19-1, -5 and -6; 166's said '-68 … left to R3, none is taken in here' and retired
2026-11-18-68, all as 'taken in'." Three entries had to be restored by hand, and every intent since
has had to avoid naming an id in those sections unless it takes the nit in. "Expected: only nits
the change says it takes in are retired, e.g. a 'Nits taken in:' line, or ids the diff's review
confirms."

2026-11-19-30 (low): "With 'yes, with a fix', the train's fix step (land-fix,
plugins/factory/scripts/landing.py: 'the builder changed nothing outside the change's folder:
nothing to commit') stops when the builder finds nothing to change, and a rerun repeats the same
stop: the only way on is train --stop and a fresh landing without the fix." Seen landing 173 with
fix R1: the stack's resolver had already rewrapped the line, and the builder rightly made no edit.
"Expected: a fix the builder reports as already satisfied, with its evidence, is recorded as such
and the train goes on to the gate and the landing review."

## Outcome

- A landing retires a nit only when the change says it takes it in; an id named for any other
  reason, in any section, retires nothing. A test lands a change that names an open nit as not
  taken and finds it still in the register.
- A landing fix the builder reports as already satisfied, with its evidence, is recorded as such,
  and the train goes on to the gate and the landing review without a stop. A builder that changed
  nothing and gave no such report still stops, as today.
- The fix still counts as a signal for the change, so a later landing never passes it by itself.
- **Moves O2:** no register entry is retired by a change that didn't take it in.
- **Moves O3:** a landing fix that turns out unneeded costs no stop and no relaunch.

## Affected

- **Area:** the factory's landing.
- **Files & components:** `plugins/factory/scripts/factory.py` (`named_nits()`, `NIT_SECTIONS`),
  `plugins/factory/scripts/landing.py` (`land-fix --commit`, and where `retired_nits` is written to
  `entries.md`), the land-fix prompt in `plugins/factory/prompts/`, `tests/test_factory.py` and
  `tests/test_train.py`, `plugins/factory/README.md`, and the intent template's or guide's words on
  naming nits if the marker moves there.
- **Downstream:** every factory landing; any host whose intents or specs name nit ids; the
  `Retired nits:` lines in commit messages and the entries a `Close` commit retires.
- **Contracts:** the register's entries are retired only inside the `Close` commit, from
  `entries.md`; `[review] sensitive` covers `landing.py`, so full depth; if the marker for a taken
  nit changes, `/sdlc:intent` (Tier 1 Approach) and core `/sdlc:ship` must say the same.

## Constraints

- A change that names its nits the way landed changes did (a "Nits taken in:" line, as 173's
  Approach has) keeps retiring them.
- Never retire on the diff's evidence alone: a nit is retired by what the change says it took in.
- This change's own spec names no open nit by id in its Requirements, or its own landing would
  retire it.

## Open questions

- ~~What marks a nit taken in: a `Nits taken in:` line in the Approach or Requirements, a section of
  its own, or ids the landing review confirms?~~ Resolved: a `Nits taken in:` line in those sections (spec R1, R2).
- ~~Does core `/sdlc:ship` need the same marker, so a change built by hand and one by the factory
  name nits alike?~~ Resolved: not to read it; the shared skills tell both to write it (spec R4).
- ~~How does the builder say a fix is already satisfied: a line in its reply the script reads, or an
  empty diff plus evidence that the asked-for state holds?~~ Resolved: both, `FIX: ALREADY MADE` with
  `## Evidence` on an empty diff (spec R5).
