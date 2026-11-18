---
id: 149
slug: landing-resolver-agent
tier: 2
impact: minor
stage: shipped
created: 2026-11-18
updated: 2026-11-18
shipped: 2026-11-18
idea:
depends_on: [146, 147]
fixes: [2026-11-18-73]
serves: [O4]
---

# 149 — A landing's conflicts are resolved by an agent of their own, measured apart from the builder

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`factory.py agent --task train-resolve` resolves a landing train's conflicts with the builder
(`agents/builder.md`) in a fresh session of its own, and its runs are recorded as the builder's:
`runs/builder.sessions`, `runs/costs.jsonl` rows with `role: builder`, and so `Sdlc-Role: builder`
on the change's `Close` commit. On 2026-11-18, 146's train resolutions in `tests/test_metrics.py`
(two, across two trains) and 147's in `tests/test_train.py` were all builder runs. The builder's
cost, time and (once 146 lands) behaviour counts then include merging work it didn't do in the
build, which skews exactly the comparisons 146 and the Fable evaluation make (one model's builder
against another's). A resolver can't have a model of its own either: `[models] builder` decides
it, though merging two finished changes is narrower work than building one. In the person's
words: "Why not create a landing agent? Specialized for merging the conflicts."

## Outcome

- A new agent, `plugins/factory/agents/resolver.md`, resolves a train's conflicts: it edits only
  the conflicted files and starts no sub-agents (`Read`, `Grep`, `Glob`, `Edit`, `Bash`; no
  `Agent`), and its instructions are about merging only: keep both changes' intent, never
  re-implement either, and say in its reply what it combined from each side.
- `train-resolve` runs it, never the builder, and its run is recorded under its own role:
  `runs/resolver.sessions`, `role: resolver` in `runs/costs.jsonl`, and its own
  `Sdlc-Role: resolver` trailer at close.
- `[models] resolver` sets its model, sonnet by default at either depth, and `start`'s
  `models_at` lists it.
- The rule that only the builder edits becomes "only the builder and the resolver edit", in
  AGENTS.md, the factory README and the test that enforces it; the resolver runs no `checks.md`
  (`test_no_agent_but_the_builder_runs_checks`).
- A test runs a train to a conflict with a stand-in `claude` and finds the resolver's agent and
  model on the run, its session and cost under `resolver`, nothing added to the builder's records,
  and a file it wasn't told about left untouched.
- **Moves O4:** a retro compares builders by model and prompt without the trains' merging work
  mixed in, and sees what resolving costs on its own.

## Affected

`plugins/factory/agents/resolver.md` (new), `plugins/factory/scripts/factory.py` (`cmd_agent`'s
`train-resolve`, the role and model tables, `DEFAULTS["models"]`), `plugins/factory/README.md` and
AGENTS.md (who edits), `scripts/metrics.py` only if a role name is listed there, and
`tests/test_factory.py`, `tests/test_train.py` and `tests/test_skills.py`. Every factory host's
landings. It waits on 146, whose per-role counts this keeps clean, and on 147, which rewrites the
train's resolve steps.

## Constraints

- The resolver never commits, pushes or merges; only the script continues the rebase, as now.
- Its edits stay inside the conflicted files: a resolution touching any other file is refused by
  the script, not trusted to the prompt.
- An old `Close` commit's `Sdlc-Role: builder`, its resolutions inside, reads the same; nothing is
  recounted.
- The landing review of a resolved conflict is unchanged: every reviewer at the run's depth still
  reads it.

## Open questions

- ~~Does the script enforce "conflicted files only" by comparing the tree after the run and
  refusing the resolution, or by the agent's tool permissions alone?~~ Resolved: the script, from
  one `git status --porcelain -z` listing (spec R8, R9).
- ~~Does `land-fix`, the person's fix while landing, stay with the change's own builder? Probably
  yes: it's a change to the work, not a merge.~~ Resolved: yes (spec R11).
- ~~Is sonnet enough for a semantic conflict (two changes editing the same function), or should the
  default be opus until the measurements say otherwise?~~ Resolved: sonnet, approved with the spec;
  the gate and the landing review catch a wrong merge.
