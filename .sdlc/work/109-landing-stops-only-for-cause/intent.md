---
id: 109
slug: landing-stops-only-for-cause
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-77
depends_on:
fixes: [2026-11-17-71, 2026-11-17-72, 2026-11-17-73, 2026-11-17-74, 2026-11-17-78, 2026-11-17-79]
serves: [O3, O6]
---

# 109 — A landing stops only for what needs the person

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

On 2026-11-17 most landings stopped on changes that had passed, or couldn't go on by themselves:

- **2026-11-17-71:** the landing's behaviour check left an exit off a trivial read, stopping 103,
  098, 104 and 107 whose verdict was `PASS`; 105 wrote its verdict on line 7.
- **2026-11-17-72:** a mend during a landing wrote into the build round (103).
- **2026-11-17-73:** a failed landing commit dropped git's error (098).
- **2026-11-17-74:** a landing that failed between ship and its commit couldn't resume (098).
- **2026-11-17-77:** an approver's or verifier's answer after a preamble had no mend (099, 107).
- **2026-11-17-78:** a carried note kept only its first line and took its whole text as the seed's
  title (63, 64, 52–59).
- **2026-11-17-79:** a landing's conflict resolution brought back the seeds its ship had deleted
  (104 re-added 37 and 38, tagged `[building]`).

Each was finished by hand, so the landing 103 and 104 built still asked the person to step in
on nearly every change.

## Outcome

- A read-only command without an exit in a landing's evidence is a mend, not a stop; a landing
  review can be mended once, its reply written to `reviews/land-<n>/`.
- A failed landing commit carries git's error, and a rerun after one makes the commit.
- An approver's or verifier's answer after a preamble gets the one mend a reviewer's does.
- A carried note reads its continuation lines, and a seed with no proposed title is titled from its
  first sentence.
- A landing's resolution of `.sdlc/work/inbox.md` never keeps an entry the change's `idea:` or
  `fixes:` names, so a seed its ship deleted stays deleted.
- Tests in `tests/test_land.py` and `tests/test_factory.py` pin each.
- **Moves O3:** a landing stops only for what needs the person.
- **Moves O6:** the factory finishes what it starts without a hand step.

## Affected

- **Area:** sdlc-factory's landing and mends.
- **Files & components:** `plugins/factory/scripts/factory.py` (`land-verdicts`, `mend`,
  `cmd_land`, `_dispose()`, `verdicts`), the behaviour and approver agents' prompts, the land and
  build skills, `plugins/factory/README.md`, tests.
- **Downstream:** every factory run and landing.
- **Contracts:** when a run stops (always Tier 2); never patching an agent's verdict (a mend is
  the agent's own reply, never an edit); landing commits only through sdlc's own steps.

## Constraints

- No supervisor edits an agent's reply.
- A second missing evidence, a red gate or a real verdict failure still stops.

## Open questions

- ~~Is a read-only command's missing exit a mend, or no stop at all?~~ Resolved: a mend, for any
  command, since the script can't tell a read from a write (spec R1).
- ~~Does a landing mend count against the same "once per role" as a build round's?~~ Resolved: no,
  once per role per landing round, recorded as `<role> land-<n>` (spec R3). The person approved
  widening the mend to the approver, the verifier and landing rounds, matching seeds by id only,
  and dropping retired nits too in R13 (R1 in `decisions.md`).
