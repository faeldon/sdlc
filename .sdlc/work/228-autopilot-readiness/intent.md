---
id: 228
slug: autopilot-readiness
tier: 2
impact: none
stage: shipped
created: 2026-11-22
opened: 2026-11-22T01:37Z
updated: 2026-11-22
shipped: 2026-11-22
idea: 2026-11-21-48
depends_on:
serves: [O6]
origin: self
---

# 228 — The autopilot loop is tested end to end before anyone runs it unattended

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Autopilot (216) lands changes with no person in the loop, and the next release is when it gets
its first real run on a host. Its tests stop short of the loop as it really runs:

- 2026-11-21-48: "`test_autopilot_end_to_end` drives the loop in process with `run_step` stood in
  for, as the train's tests do. … `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does`
  runs a real `run_step` child under the lock, but no test runs the whole loop's subprocesses
  with a stand-in `claude`."
- 2026-11-21-54 (security review, value med): "no test that a host's `[commands] check`, run by a
  `gate` step under the loop, lacks `AUTOPILOT_RUN_ENV`/`TRAIN_RUN_ENV`; `take_markers()` is
  untested". That is the guard that keeps a host's own code from passing `--by autopilot`.
- 2026-11-21-53: the "agent is refused" half of the real-step test calls `agent_env()` directly
  rather than going through `_claude`.
- 2026-11-21-51: `cmd_answer` (factory.py:2511), which autopilot calls for every default it
  answers, reads and rewrites `decisions.md` with no lock, "safe only because one step runs per
  change at a time", and nothing says so.
- Landing and decision records autopilot leans on: 2026-11-22-2 (`_record_land()` runs before
  `record_closes()`, so a refused agent leaves a landing step recorded), 2026-11-22-1
  (`recorded_closes()` rereads the whole ledger on every agent run), and 2026-11-22-11
  (`BUILT_RE` counts a `- BUILT:` line quoted inside a code fence as built, which autopilot's
  `hold_causes()` now reads, since 218).

## Outcome

- A test runs `autopilot --run` as a real subprocess, every step its own child, with a stand-in
  `claude` on `PATH`, from a seed to a landed change in a scratch repo, and asserts the
  `Sdlc-Landed: by=autopilot` trailer, the `opened_by: autopilot` intent and the `→ decided by
  autopilot:` lines.
- A test shows a host's `[commands] check` run by a loop's `gate` step sees neither marker, and
  `take_markers()` has a test of its own; the refused-agent test goes through `_claude`.
- `cmd_answer`'s lack of a lock is either made safe or stated where it's relied on.
- A refused agent leaves no landing step recorded; a fenced `- BUILT:` line isn't counted.
- **Moves O6:** the first unattended autopilot run on a host is one whose whole loop a test has
  already driven.

## Affected

- **Area:** the factory's autopilot loop and the landing records it reads.
- **Files & components:** `tests/test_autopilot.py` (most of the change), `plugins/factory/scripts/
  factory.py` (`cmd_answer`, `cmd_agent`'s order, `recorded_closes`, `BUILT_RE`), possibly
  `plugins/factory/scripts/autopilot.py`.
- **Downstream:** every host that runs `/sdlc-factory:autopilot`; nothing it writes changes shape.
- **Contracts:** `autopilot.py` is `[review] sensitive`; the markers' rule (only `loop_env()` gives
  them back, to a loop's own children); the records ledger vouches for what it writes first;
  no test may reach the network or a real `claude`.

## Constraints

- The stand-in `claude` must be a fake on `PATH`, as the train's tests use: no paid run, no network.
- The end-to-end test must stay fast enough for `pytest -n auto`, and be skipped (not failed) where
  its shebang fakes can't run (Windows, not `portable`).
- No behaviour change for a person's runs: the order and lock fixes keep every output the same.

## Open questions

- ~~Does `cmd_answer` get a lock (on what: the change folder, or the git common dir's main lock), or
  only a comment naming why one step at a time makes it safe?~~ Resolved: a docstring stating the
  rule, pinned by a test that no ledger writer runs beside another step of its change (spec R5).
- ~~Is `recorded_closes()`' reread worth caching, or is the nit accepted as negligible, as its own
  text says?~~ Resolved: no cache; the cost is stated and a one-read-per-agent-run test pins it
  (spec R7).
- ~~Which loop path does the end-to-end test drive: one clean seed to a landing, or also a hold
  (`hold_causes()`) and a park?~~ Resolved: one clean seed to a landing, with a real
  `answer --by autopilot` on the way; holds and parks stay covered in process (spec R1).
