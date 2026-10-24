---
id: 008
slug: drift-gate
tier: 1
impact: none
stage: shipped
created: 2026-10-24
updated: 2026-10-24
shipped: 2026-10-24
idea: This repo's gate fails when its setup record drifts
depends_on:
serves: none
---

# 008 — This repo's gate fails when its setup record drifts

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

This repo is a host of its own plugin: `.sdlc/SDLC.md` and `.sdlc/REVIEW.md` are its copies of
`defaults/SDLC.md` and `defaults/REVIEW.md`, and `.sdlc/setup.json` records a hash of each default
block they were set up from. A change that edits a default must run `sdlc.py record` by hand to
refresh that record, and nothing fails when it forgets: `./check.sh` passes, ship passes, and the
drift surfaces later as a `warn` in `setup`'s readiness report.

It has already cost a change. `f341a83` ("Refresh the sdlc setup for 1.0.0") refreshed the record
after the fact, straight on `main`, outside any change; and 005-acceptance-checks had to be rebased
and shipped again before it could close (its `Close` commit records `ship_runs=2 reenter=1`).
Nearly every change edits a default, so this is a trap any of them can step in.

## Outcome

- `./check.sh` fails when `sdlc.py drift` on this repo reports anything at all in `breaking`,
  `refresh` or `report`, with a message naming the drifted docs and blocks and saying to run
  `sdlc.py record`.
- On today's `main`, where `drift` reports nothing in any of the three, the test passes.
- Editing a block in `defaults/SDLC.md` without running `record` fails the gate in that same
  change, before ship.

## Affected

- **Area:** this repo's test suite only.
- **Files & components:** a new test, likely in `tests/test_defaults.py` beside the test that keeps
  `.sdlc/SDLC.md` and `.sdlc/REVIEW.md` tracking the defaults; it calls `drift()`
  (`scripts/sdlc.py:4225`) on the repo root. No change to `drift()` itself expected.
- **Downstream:** whoever runs `./check.sh` here: every change's gate at ship, and close's `verify`
  step. Hosts see nothing: the test isn't shipped behaviour and doesn't run in their repos.
- **Contracts:** "This repo's process docs track the defaults" (AGENTS.md), which this extends from
  headings and bullets to the setup record; `drift()`'s three-way comparison, which the test reads,
  never redefines.

## Constraints

- The test must pass in a change's worktree as well as in the main checkout, so it reads the
  checkout it runs in, not `main_root()`.
- It must not write anything: `record` stays a deliberate step the change takes, and the test only
  says when it was missed.
- `report` entries fail the gate too. A default edit to a block this repo rewrote in its own
  words is a `conflict`, and conflicts land in `report`, not `refresh`. Right after `record`,
  the only `report` entry left would be an unknown config key, which is a real problem anyway.

## Open questions

- ~~Does the release's version bump in `plugin.json` make `drift` report a version mismatch
  against `setup.json`'s recorded version?~~ Resolved: no. The version adds a `report` entry only
  when the record is newer than the plugin (`_older(plugin, version)`), never after a bump.
- ~~Should a failure print the `record` command, or is the drift JSON enough?~~ Resolved: it
  prints the command, run from the change's own checkout, and one line per drifted block.

## Approach

One test that calls `sdlc.drift(<repo root>)` and asserts `breaking` and `refresh` are empty, with
a failure message that lists the drifted blocks and the `uv run --script scripts/sdlc.py record`
command. Settle the release question first by running `drift` against a bumped version in a
scratch copy. Add a line to AGENTS.md's "This repo's process docs track the defaults" invariant
that the setup record is kept current too, and the gate checks it.
