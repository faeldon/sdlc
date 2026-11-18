---
id: 130
slug: retro-pruning-pass
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-17-87
depends_on:
serves: [O4]
---

# 130 — Retro proposes a pruning pass over the test suite

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Nothing ever looks again at the tests already in a suite: one whose code was rewritten, one a
newer test repeats, one that passes for the wrong reason, the slowest. 118 carried it from
2026-11-12-2's third bullet, and its spec set it aside for want of per-test run times and a
test-to-code map no host records today. This repo's own gate now runs 2336 tests in about 60s.

## Outcome

- `/sdlc:retro` proposes a pruning pass when the evidence calls for one, naming candidate tests and
  why each is one; it deletes and edits no test.
- The evidence it rests on is recorded, or the pass says it can't run.
- **Moves O4:** the retrospective proposes test-suite work from evidence, not habit.

## Affected

- **Area:** the retrospective.
- **Files & components:** `scripts/retro.py`, possibly a host's `retro.evidence` or a
  `[commands]` key, the retro report template, `docs/REFERENCE.md`.
- **Downstream:** every host's retro.
- **Contracts:** retro writes only its report and the docs its commit holds; the plugin knows
  nothing of a host's test runner; `metrics.py` and `indicators.py` stay pure.

## Constraints

- Never a test edited or deleted by the retro; per-test times come from the host, if it records
  them.

## Open questions

- ~~Where per-test times come from: a host command, pytest's `--durations`, a JUnit file?~~ Resolved: host commands in `[retro] test_times`, each printing JUnit XML (spec R1–R5).
- ~~Is a test-to-code map needed, or are blame and age enough?~~ Resolved: neither; co-change history shows a test whose code moved without it (spec R7–R8), and the rest is `unmeasured` (R9).
- ~~A retro proposal, or a seed retro files?~~ Resolved: one finding whose disposition is one seed naming every candidate (spec R11).
