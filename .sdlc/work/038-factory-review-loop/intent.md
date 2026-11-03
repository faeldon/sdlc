---
id: 038
slug: factory-review-loop
tier: 2
impact: minor
stage: shipped
created: 2026-11-04
updated: 2026-11-04
shipped: 2026-11-04
idea: 2026-11-03-9
depends_on:
serves: [O3]
---

# 038 — The factory's review rounds verify, converge and scale to risk

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The factory's review loop (`plugins/factory/skills/build/SKILL.md` Step 3, `factory.py verdicts`)
runs the same way on every change, and nothing in it stops it going in circles:

- **Every `- CHANGE:` line is reworked, verified or not.** The builder addresses every
  `VERDICT: CHANGES` a reviewer wrote, including requests a reading of the code would show wrong or
  style-only. The post's point: "a person can wave off a nit in seconds. An agent fixes it", and
  each unverified request costs a rework, a commit's worth of churn and a round.
- **Rounds don't converge.** Round 2 and later reviewers read the whole change again, so they can
  raise new points on code round 1 passed, or one already answered. Nothing tells them which code
  the change didn't touch, so a pre-existing problem becomes a `CHANGE:` the builder must fix
  rather than a finding filed for later (035's `pre-existing` rank). At the cap of three rounds the
  approver only gives a verdict; it never asks the person to step back and reconsider the approach,
  which is what a loop that didn't converge usually needs.
- **One depth for every change.** `factory.toml` sets one `reviewers` list and one `rounds` for all
  of them. A README-sized change pays for three reviewers over three rounds; a change to a path in
  `[review] sensitive` (036) gets no more than any other, though `/sdlc:ship` will give it the deep
  review after.

This takes in seeds 2026-11-03-9, -10 and -11 together, as phase 4a. Seeds -12, -13 and -14 stay
for later changes.

## Outcome

- Between a round's reviews and its rework, each `- CHANGE:` line is checked against the code; only
  confirmed ones reach the builder, and `factory.py` records the dropped ones and why in the
  round's files, where `/sdlc:ship` can read them and close measures them.
- From round 2, each reviewer gets the rework's diff and the round's open `CHANGE:` lines, not the
  whole change again; a point already raised and answered is never raised again; a point on code
  the change didn't touch is reported as pre-existing, never as a `CHANGE:`.
- When the cap is reached with changes still open, the approver's decision asks the person to
  reconsider the approach, and says so in `decision.md`.
- The build question names the reviewers and rounds this change gets and why: fewer for a change
  touching no sensitive path, all of them for the full rounds for a sensitive one, with
  `max_runs` following.
- Seeds 2026-11-03-9, -10 and -11 all leave the register when this ships.
- **Moves O3:** fewer factory runs reach the round cap and escalate, and a low-risk change takes
  fewer agent runs, so the person stops at the factory's one question and ship's, and no more.

## Affected

- **Area:** the optional `sdlc-factory` plugin's build loop.
- **Files & components:** `plugins/factory/scripts/factory.py` (`verdicts`, `read_rounds`,
  `max_runs`, `load_config`, perhaps a verify step and round snapshots),
  `plugins/factory/skills/build/SKILL.md` (Steps 0–3 and its WAIT question),
  `plugins/factory/agents/reviewer-*.md` and `approver.md`, perhaps a new verifier agent,
  `plugins/factory/README.md`, `docs/REFERENCE.md`, `AGENTS.md`, `/sdlc:ship`'s Step 0 where it
  reads the factory's files, and the factory's tests.
- **Downstream:** hosts that install `sdlc-factory` and run `/sdlc-factory:build`; hosts without
  it see nothing. `/sdlc:ship` reads the round files a run leaves.
- **Contracts:** agents that judge have no `Write`, only the builder edits, nothing commits; one
  WAIT in the build skill, its wording changed; the factory's cached copy has no `sdlc.py`, so
  `factory.py` reads what it needs itself; `sdlc` only reads the files a run leaves; narrow
  `allowed-tools`; nothing commits, so round snapshots are never commits.

## Constraints

- A host with no `[review]` lists and the default `factory.toml` gets no less review than a plain
  low-risk run today; whether its default stays as now is an open question.
- No agent but the builder writes code, and nothing in the loop commits, stashes on the shared
  stack, or pushes.
- The build skill's one approval still bounds the run: the most agent runs it states is never
  exceeded.

## Open questions

- ~~Who verifies a `CHANGE:` line: a new read-only verifier agent, the approver, or the builder
  told to verify before reworking? And how many votes make it confirmed?~~ Resolved: one new
  read-only verifier agent a round, the person's call (spec R1–R3).
- ~~How does `factory.py` read risk, the cached copy having no `sdlc.py`: `.sdlc/config.toml`'s
  `[review]` and the diff itself, from the base branch as 036 does?~~ Resolved: from the diff after
  round 1's build, `[review] sensitive` read from the base branch, a pinned copy of the matcher;
  the timing the person's call (spec R8).
- ~~What the depths are: what a low-risk change runs (one reviewer for one round, or the code
  reviewer alone), and whether `factory.toml` can override them.~~ Resolved: `[light]`, default the
  code reviewer for two rounds, overridable; no sensitive list keeps every run full (spec R9–R10).
- ~~Round snapshots: `git write-tree` of the index or `git stash create`, neither landing on the
  shared stash stack or as a commit; where is the snapshot's id recorded?~~ Resolved: neither; a
  file of path hashes in the change folder (spec R4).
- ~~What ship and close read of dropped findings: a count in the round files, a new
  `Sdlc-Review` field, or both?~~ Resolved: both (spec R12–R13).
