---
id: 073
slug: factory-script-gate
tier: 2
impact:
stage: design
created: 2026-11-17
updated: 2026-11-17
idea: 2026-11-17-8
depends_on:
serves: [O6, O5]
---

# 073 — Run the gate as a script step before a factory round's reviewers

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The factory learns whether a build works from agents' replies. The builder reports that it ran
the repo's gate, and `reviewer-behaviour` runs `[commands] check` in parallel with the other
reviewers. `factory.py` checks only that each reply ends with an `## Evidence` block
(`read_evidence()`), not what the command was or whether it passed. That causes three problems:

- **A failing build still costs a full round.** At the full depth, code, security, test and
  behaviour all review it, then the verifier checks their changes, before the builder hears the
  gate is red. At the defaults that is up to 5 agent runs spent on a build that a single exit code
  would have sent straight back.
- **The light depth has no independent gate at all.** `[light]` runs only `reviewer-code`
  (`DEFAULTS["light"]`), so on a diff touching no sensitive path, "the gate passes" is the
  builder's own word. A light run is exactly the case 072's self-passing landing wants to trust.
- **A change can weaken what it is judged by.** The gate is read from `.sdlc/config.toml` in the
  change's own worktree, and the script it runs (here `./check.sh`) is a file in that tree.

The factory it learned from runs the repo's checks as a script step before any reviewer is
spawned, and again before merging. In its example run, that step caught a builder editing a
protected file in round 1. Raised as seed 2026-11-17-8.

## Outcome

- After each builder report, `verdicts` names a new step, `gate`, before `review`.
  `factory.py gate <NNN>` runs the gate command itself, in the change's worktree. It reads the
  command from the base branch's config, so a change can't edit the command it is judged by. It
  files the exit, duration and output tail under the round.
- A red gate resumes the builder with that file, through `factory.py agent`, as a rework does. No
  reviewer or verifier starts on a red build. A green gate goes on to `review`.
- The light depth gets the same gate as the full one, so a light run is never green on an agent's
  word.
- `reviewer-behaviour` keeps the spec's end-to-end path and stops running the gate, which the
  script now owns.
- `/sdlc:ship` shows each round's gate results with the verdicts.
- **Moves O6:** a factory change reaches its reviewers only on a gate the script saw pass, so its
  record of passing checks is the script's, not an agent's.
- **Moves O5:** a factory change whose build fails costs one builder run per red gate instead of a
  round of reviewers and the verifier, which shows in the change's agent runs at close.

## Affected

- **Area:** `plugins/factory/` (`sdlc-factory`).
- **Files & components:**
  - `factory.py`: a new `gate` command, the `gate` step in `loop_state()`, `max_runs()`, and the
    prompt for a gate rework in `cmd_agent()`.
  - `skills/build/SKILL.md`: its allowed-tools rule for `factory.py gate`, Step 1's account of the
    run, the WAIT question, and the `gate` branch of the loop.
  - `agents/reviewer-behaviour.md` and `agents/builder.md`.
  - The factory's tests, and the factory README's "Rounds that converge" and Mechanism sections.
- **Downstream:**
  - Every host with `sdlc-factory` installed: its factory runs gain a step and lose a gate run
    from the behaviour reviewer.
  - `/sdlc:ship` and `/sdlc:close` read the files a run leaves. Close's `measure` counts rounds
    into `Sdlc-Rework`, so what a red gate counts as must be decided here.
  - 072-factory-land, open, edits `factory.py` too and reruns the gate before it lands a change.
    Whichever lands second rebases over the other, and they might share one gate step.
- **Contracts:**
  - An `allowed-tools` rule for a command that writes and runs a host command unasked.
  - The build skill's WAIT question, which must name the step.
  - Rules the change must keep: agents that judge have no Write, only the builder edits, and
    nothing commits; `factory.py` stays self-contained, its `_sh()` copy pinned to `sdlc.py`'s;
    `test_no_agent_but_the_builder_runs_checks`; the scripts run on Windows (`encoding="utf-8"`,
    `errors="replace"` for a host's command).

## Constraints

- The gate command comes from the base branch's `.sdlc/config.toml`, never from the change's
  checkout, as `[review] sensitive` and `factory.mode` already do.
- The gate step must not leave the tree changed. If the gate command dirties the tree, that is a
  failure, as for `accept`.
- `checks.md` is still never run by the gate step or any agent. Only `accept` runs it, under a
  prompt.
- A red gate never skips the review on the build that comes back green. Every build that reaches
  the approver has been reviewed at its depth.
- The round limit still bounds a run: a builder looping on a red gate can't run forever.
- Existing run folders still read. A round recorded before this change, with the behaviour
  reviewer's gate run and no gate file, is not a problem.

## Open questions

- ~~Does a red gate count against `rounds`?~~ Resolved: no, it has its own cap of 2 fixes a
  round, then a stop; `max_runs()` adds the fixes, and `Sdlc-Rework` gains `gate_fail` (spec R5,
  R10).
- ~~Where does the gate's file go?~~ Resolved: `build/round-<N>.gate.md`, since sdlc counts every
  file under `reviews/round-<N>/` as a reviewer; ship reads it as the script's record (R2, R10).
- ~~Can a change weaken the gate script itself?~~ Resolved: the command is the base branch's; the
  script it runs is the change's, a gap documented, guarded by `[review] sensitive` (Design).
- ~~What happens with no `[commands] check`?~~ Resolved: the step is skipped and says so (R6).
- ~~What is the gate's timeout, and what does a timeout count as?~~ Resolved: 30 minutes, and a
  timeout is a FAIL (R1, R2).
- ~~Does the builder still claim the gate in its `## Evidence`?~~ Resolved: it may run it, and the
  script's file is the record (R8).
- ~~Should 072's pre-land gate and this step be one `factory.py gate`?~~ Resolved: yes; whichever
  lands second wires `factory.py gate` into land (R12).
