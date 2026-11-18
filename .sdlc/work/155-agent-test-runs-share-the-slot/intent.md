---
id: 155
slug: agent-test-runs-share-the-slot
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on: [149]
serves: [O5]
---

# 155 — Agents' test runs share the machine with the gate

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Agents' own test runs share the machine with the gate. Builders and reviewers run `./check.sh` or
`pytest -n auto` themselves, outside the `gate_jobs` slot that only `factory.py gate` and
`sdlc.py gate` take. On 2026-11-18 five builds ran in parallel (149, 150, 151, 152, 154): four full
suites ran at once, each with a worker per core on an 18-core machine, and 152's gate, about 2
minutes alone, took 527 seconds. Most of those runs repeat proof already made: the script's gate
runs the whole suite on every build before any reviewer reads it, yet the builder runs it again for
its `## Evidence`, and the code, test and behaviour reviewers often run it once more.

## Outcome

- Fewer runs: a builder runs the tests near its change and cites the gate record
  (`build/round-<N>.gate.md`) for the whole suite, rather than running it again; reviewers read the
  gate record instead of rerunning the suite, and run only the targeted tests their verdict rests
  on. The agents' prompts say so, and `is_read()` and the evidence rules accept a citation of the
  gate record.
- A slot for the full runs that remain: `factory.py check NNN` waits for one of `gate_jobs` slots,
  then runs the base branch's `[commands] check` in the change's worktree; agents are told to use it
  in place of a bare `./check.sh`. A test starts two at once with one slot and finds the second
  waits.
- With five builds in parallel, no more full suites run at once than `gate_jobs`; 146's per-role
  `test_runs=` shows the drop.
- **Moves O5:** running several factory builds at once doesn't slow every gate several times over,
  and the factory spends fewer runs proving what its gate already proved.

## Affected

`plugins/factory/scripts/factory.py` (a new `check` command, the evidence rules), the agent prompts
(`builder.md`, `reviewer-code.md`, `reviewer-test.md`, `reviewer-behaviour.md`),
`plugins/factory/README.md`, and `tests/test_factory.py`. Every factory host's runs. It waits on
149, which edits `builder.md` and the agent tables.

## Constraints

- The script's gate stays the one proof the whole suite passed on a build; an agent's narrower run
  never replaces it.
- A behaviour check still runs the spec's end-to-end path itself: that isn't the suite, and it
  stays.
- `check` takes the same slot locks as `gate`, in the git common dir, never `sdlc.lock`, and frees
  them however it ends.
- No agent gets a permission it lacks today: `check` runs only the base branch's
  `[commands] check`.

## Open questions

- ~~Does a builder still run the full suite once before its first report, through the slot, or rely
  on the gate entirely?~~ Resolved: it may, through `factory.py check`, but isn't told to; the gate
  that runs next proves the suite (spec, Design).
- ~~How does an agent find the tests "near its change": by the paths it touched, or by naming them
  itself?~~ Resolved: it names them itself; the plugin knows nothing of a host's test layout (spec,
  Design).
- ~~Should `-n auto` become `-n <cores ÷ gate_jobs>` for this repo's own gate, as a third, cheaper
  part?~~ Resolved: left out, as this repo's own `check.sh` policy, not the plugin's (spec,
  Alternatives rejected).
