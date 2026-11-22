---
id: 229
slug: park-hardening
tier: 1
impact: none
stage: shipped
created: 2026-11-22
opened: 2026-11-22T01:37Z
updated: 2026-11-22
shipped: 2026-11-22
idea: 2026-11-21-29
depends_on:
serves: [O6]
origin: self
---

# 229 — A park can't be set up to swallow red checks, or write control characters to a terminal

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Parking (222) ships new in this release, and an unattended autopilot run is what waits on it.
222's reviews left five rough edges, and one docs gap is filed beside them:

- 2026-11-22-16 (security): "`[park] exit = 1` is accepted, which makes every ordinary red check a
  park": a host that sets it turns every failed gate into a wait, never a red.
- 2026-11-22-15 (security, value med): "`busy_of()`'s `clean()` keeps control characters (ESC and
  the like), which reach `status` in the terminal". The busy lines are a host command's output.
- 2026-11-22-13: `needs_of()` (sdlc.py:5164) compares `now` with the park's own `DEADLINE`, not
  the deadline cut to `[park] deadline` that `verdicts` uses, so the board can show no need for a
  park `verdicts` has already stopped.
- 2026-11-22-14: `park --clear` checks only expiry, not `vouched`, so an unvouched record needs
  an `rm` the refusal doesn't name.
- 2026-11-22-17: the slot-wait test only asserts "didn't run" on stderr, not the "slot" wording.
- 2026-11-21-29: AGENTS.md's *Skills* invariant lists the skills that owe a WAIT and leaves out
  `update`, which `tests/test_skills.py`'s `GATED` includes.

## Outcome

- `[park] exit` refuses (or warns on) `0` and `1`, and the factory README says 75 is the one to use.
- `busy_of()` strips C0 and C1 control characters before a busy line is stored or shown.
- `needs_of()` reads the park's deadline capped as `verdicts` caps it.
- `park --clear` removes an unvouched record too, or its refusal names the `rm`.
- The slot-wait test asserts the "slot" wording.
- AGENTS.md's *Skills* list names `update`.
- **Moves O6:** a parked autopilot change waits only on a real busy answer, and what it prints is
  safe to show.

## Affected

- **Area:** the factory's park handling, and the map.
- **Files & components:** `plugins/factory/scripts/factory.py` (`busy_of`, the `[park]` config
  read, `cmd_park`), `scripts/sdlc.py` (`needs_of`), `plugins/factory/README.md`,
  `tests/test_factory_park.py`, `AGENTS.md`.
- **Downstream:** hosts that set `[park]`. None does yet, since it is unreleased.
- **Contracts:** `[park] exit` is a config key a host may set; refusing `1` narrows it before any
  release ships it, so no host loses a value it had.

## Constraints

- A host without `[park] exit` sees no change (222's R1).
- `needs_of()` stays the one place the board's and `status`' needs are decided.

## Open questions

- Refuse `exit = 1` (and `0`), or only warn?

## Approach

In `factory.py`, refuse a `[park] exit` of 0 or 1 where the config is read, and strip
`\x00-\x1f\x7f-\x9f` (keeping none) in `busy_of()`'s `clean()`; let `park --clear` remove an
unvouched record; in `sdlc.py`, cap the deadline in `needs_of()`'s caller as `verdicts` does.
Assert the slot wording in `tests/test_factory_park.py`, add `update` to AGENTS.md:366's list,
and say 75 in the factory README's `[park]` block.

Nits taken in: 2026-11-22-13, 2026-11-22-14, 2026-11-22-15, 2026-11-22-16, 2026-11-22-17
