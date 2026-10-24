---
id: 007
slug: stop-target
tier: 2
impact: major
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea:
depends_on:
serves: [O3]
---

# 007 — Reconcile O3's two-stop target with the gates a change passes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

O3 (Few stops) says each change should cost its person "one at spec and one at ship", and
`metrics.target_stops` defaults to 2 (`scripts/sdlc.py:220`). The same 2 applies to every tier and
way of running. But the gates the process itself requires are more than that:
- `REQUIRED` in `scripts/metrics.py:98` lists 3 WAITs for a Tier 1 change by hand (intent, ship,
  close) and 5 for Tier 2 (intent, spec, plan, ship, close);
- the factory's two lists have 5 each.

So a change that stops only where the process makes it stop is already one to three stops over
target. The first retrospective (2026-10-24, `a9ad7ee`) measured median stops of 6 for Tier 1 and
13.5 for Tier 2, against a target of 2 for both. That makes the gap unreadable: nobody can tell
from the numbers how much of it is the gates and how much is extra questions and permission
prompts. G2 and M2 in `.sdlc/DIRECTION.md` can't be judged against a target the design rules out.

## Outcome

- A change is measured against a target it can meet by stopping only at its gates. The target is
  set per tier and way of running, as the required gates plus a stated allowance, so a stop above
  it is a real extra.
- Close's trailers and `retro`'s `metrics` report that target per group, and the stops above it,
  so the next retrospective can say how far each tier is from O3.
- O3's measure in `.sdlc/PRODUCT.md` says the same thing in words, and the process doc's "Signals
  worth watching" agrees.
- A host that set `metrics.target_stops` keeps a meaning for it, or is told what changed.
- `./check.sh` passes.
- **Moves O3:** a change that stops only at its gates reads as on target, so the stops a
  retrospective calls extra are the questions and prompts worth cutting, not the gates themselves.

## Affected

- **Area:** the metrics close records and retro reads, the config they read, and the product and
  process docs.
- **Files & components:**
  - `scripts/metrics.py` (`REQUIRED`, where `target` is set on the totals);
  - `scripts/sdlc.py` (`CONFIG_KEYS["metrics"]["target_stops"]` and its validation, and `retro`'s
    `metrics` groups);
  - `.sdlc/PRODUCT.md` O3;
  - `defaults/SDLC.md` and `.sdlc/SDLC.md` (*Signals worth watching*);
  - `docs/REFERENCE.md` (*Metrics*, the config sample);
  - `tests/test_metrics.py` and `tests/test_retro.py`.
- **Downstream:**
  - every host's `Close` commits, through the `Sdlc-Totals` trailer that carries `target=`;
  - `/sdlc:retro` reading those trailers, including ones written before this change;
  - a host that set `target_stops` in its config;
  - this repo's `.sdlc/DIRECTION.md` M2, whose `Groups:` line names this change by title.
- **Contracts:**
  - **The trailer format and event list are a contract:** extend them, never redefine
    (`AGENTS.md`, *Metrics*). Old `Close` commits carry `target=2` and must still read.
  - **A config key's meaning changes** (always Tier 2).
  - **Measuring never refuses.**
  - **The defaults and this repo's copies move together.**

## Constraints

- **The gates stay as they are:** no skill's WAIT changes.
- **Only reconcile:** cutting the stops above the gates (extra questions, permission prompts) is
  out of scope, for a later change once the measure means something.
- **History stays readable:** a `Close` commit written before this change still parses, and
  `retro` doesn't misread its `target=2`.
- **The product doc's users, problem and bets are left alone;** only O3's measure is rewritten,
  and only as the person approved here.

## Open questions

- ~~What is the allowance above the required gates?~~ Resolved: 1, at every tier, so a
  Tier 1 change's target is 4 (5 with plan mode) and a Tier 2's is 6.
- ~~Is the target computed, or configured?~~ Resolved: computed per change as its gates plus a
  new `metrics.stop_allowance`; `target_stops` is retired.
- ~~What happens to a host's existing `target_stops`?~~ Resolved: it is listed in
  `RETIRED_KEYS`, so `drift` reports it as breaking with the fix; the release is major.
- ~~How do old and new trailers read side by side?~~ Resolved: `target=` keeps its name and
  meaning (the target the change was measured against), `allowance=` is added, and retro
  recomputes an old commit's target from its own `required=`.
- ~~Should permission prompts count as stops?~~ Resolved: they already don't; close reports
  them apart.
- ~~What does O3 say?~~ Resolved: it names the gates per tier and allows one more (spec, R5).
