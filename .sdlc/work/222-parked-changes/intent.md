---
id: 222
slug: parked-changes
tier: 2
impact: minor
stage: shipped
created: 2026-11-21
opened: 2026-11-21T14:26Z
updated: 2026-11-22
shipped: 2026-11-22
idea: 2026-11-21-45
depends_on: [216]
serves: [O6]
origin: self
---

# 222 — A change can be parked on a host resource, with a deadline, instead of stopping or asking

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From seed 2026-11-21-45: "Autopilot (216) runs changes unattended, but a host step can need a
resource another change holds: a shared deployment, a database object, an environment one change
at a time may use. Today the factory has two answers, a blocking decision (the person is asked) or
a stop, and neither suits a wait that resolves itself in minutes. Nothing either says how long a
change may wait."

## Outcome

- **A host step can answer busy:** a host command the factory runs (or a builder runs through the
  host's own task) exits with a documented code meaning "waiting on a host resource", with who
  holds it and until when. The factory then **parks** the change, neither stopping nor asking.
- **Parked is a derived state, like every other:** `runs/parked.md` holds the resource, since and
  the deadline; `verdicts` reads it as `next: parked`, then the step it interrupted once the host
  says free, or `stop` (way: ask the person, naming the holder) once the deadline passes. A crash
  or restart reads the same state from the files, as now. The board and `/sdlc:status` show it as
  `stopped.md` is shown.
- **No resource model in the plugin:** which resources exist, how they're locked, and what
  conflicts with what stay the host's. The plugin learns only "busy, until".
- **A transition table** in the docs and tests: every state the factory can be in (stage, and the
  step `verdicts` names), what moves it on, and the timeout of each waiting state (`decide`, a gate
  slot, `parked`), so nothing in it can wait forever.
- **Moves O6:** an unattended run waits out a busy host resource on its own, and stops for the
  person only when the wait runs past its deadline.

## Affected

- **Area:** the factory's run state and its scheduler.
- **Files & components:** `plugins/factory/scripts/factory.py` (`verdicts`, `_run_check()`),
  `plugins/factory/scripts/run_state.py`, `plugins/factory/skills/build/SKILL.md`,
  `plugins/factory/skills/autopilot/`, `scripts/board.py` and `status` (showing it),
  docs/REFERENCE.md and the factory README.
- **Downstream:** hosts whose checks share resources; autopilot's queue; the board.
- **Contracts:** a host's command's exit codes gain a meaning (a new documented code, opt-in);
  `verdicts` decides from the files alone.

## Constraints

- A host that never returns the busy code sees no change.
- Every waiting state has a timeout; none waits forever.

## Open questions

- ~~The exit code and the payload a host returns.~~ Resolved: opt-in `[park] exit` on the base
  branch, no default (75 suggested), and three optional `SDLC-BUSY-*` lines (spec R1, R3)
- ~~Where the deadline comes from: the host's answer, a factory default, a config key.~~ Resolved:
  the base branch's `[park] deadline` (default 60 minutes); the host's `UNTIL` sets only the next
  retry (spec R4)
- ~~Whether a parked change gives up its gate slot.~~ Resolved: it does, since a busy gate's
  process ends and frees its `flock`; a slot wait is now bounded too (spec R12)
- ~~How autopilot's queue orders parked changes against new ones.~~ Resolved: a parked change still
  counts in `in_flight` and retries in its order once its `retry` comes (spec R15)
