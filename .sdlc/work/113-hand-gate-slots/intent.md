---
id: 113
slug: hand-gate-slots
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-63
depends_on: [111]
serves: [O5]
---

# 113 — The hand gate shares the factory's gate slots

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-63:** `sdlc.py gate` (the hand gate, 091) takes no `gate_jobs` slot. 101 added
`gate_jobs` so the factory's gates run one at a time (`./check.sh` runs `pytest -n auto` across
every core), but a hand gate run beside a factory gate still runs at once with it. 101's spec left
it out by its boundary: sharing the slots would make the lock files' names a contract between
`sdlc` and `sdlc-factory`, which today read each other's files only through pinned copies.

## Outcome

- A hand gate and a factory gate never run at once beyond `gate_jobs`: the hand gate waits for a
  slot, and says it is waiting.
- The slots' lock files are named in one place each side reads, pinned by a test that fails when
  either side's copy drifts, as `risk_paths()` is.
- Without `sdlc-factory` installed, the hand gate runs as it does today.
- Tests in `tests/test_hand_gate.py` and `tests/test_factory.py` pin the shared slot.
- **Moves O5:** two gates no longer fight for the machine's cores.

## Affected

- **Area:** the hand gate and the factory's gate.
- **Files & components:** `scripts/sdlc.py` (`cmd_gate()`), `plugins/factory/scripts/factory.py`
  (the `gate_jobs` slots), `tests/test_hand_gate.py`, `tests/test_factory.py`, `docs/REFERENCE.md`
  where it describes the hand gate.
- **Downstream:** anyone who runs `sdlc.py gate` while the factory runs.
- **Contracts:** `factory.py` never imports `sdlc.py`, and each reads the other's files with
  pinned copies; the gate's slots lock in the git common dir, never `sdlc.lock` (AGENTS.md).

## Constraints

- No import between the two scripts; the lock's name becomes a pinned copy, not a shared module.
- A hand gate never fails because the factory's slots are busy; it waits, with a limit it names.

## Open questions

- ~~Is `gate_jobs` read by `sdlc.py` from `.sdlc/factory.toml`, or does the hand gate take one slot
  of whatever the factory set?~~ Resolved: read from the base branch's `.sdlc/factory.toml` through
  a pinned copy of `_gate_jobs()` (spec R3); the person approved widening AGENTS.md's factory
  paragraph for it.
- ~~How long does a hand gate wait before saying so and giving up?~~ Resolved: it says so at once,
  and gives up after 30 minutes (`SLOT_WAIT = GATE_TIMEOUT`), writing nothing (spec R1, R4).
