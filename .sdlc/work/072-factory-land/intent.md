---
id: 072
slug: factory-land
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-10-1
depends_on:
serves: [O6, O3]
---

# 072 — Land a batch of ready factory changes with one stop, or none when nothing is risky

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Since 070, the supervisor carries a factory change to "ready to ship" and stops; landing it still
takes the person two gates, `/sdlc:ship` then `/sdlc:close`, each typed in the change's worktree.
Each landing moves `main`, so the next ship's `sdlc.py base` refuses on any file both touched, and
the person resolves it by hand (commit the work, rebase, ship again), as 070 itself did behind 068.
With N ready changes, `factory.py ready` lists the order, but it is 2×N gates and a manual
conflict at every overlap. And seed 2026-11-10-1's case: a gate should pass itself when nothing
about the change is risky (no `[review] sensitive` or `irreversible` path, impact below `major`,
no open blocking decision, no ESCALATE, no Important finding, the gate green), where today every
factory change stops for every yes.

## Outcome

- `/sdlc-factory:land`, from a session of its own in the main checkout, takes the ready changes as
  one batch in `factory.py ready`'s order. For each, in turn: commit it, bring it up to date with
  `main`, resolve any conflict with the change it collides with, rerun the gate when `main`
  moved, and close it (fast-forward, archive, folder off `main`, worktree and branch removed),
  each close pushing as `git.push` says.
- The person is asked once for the whole batch, its review findings and conflict resolutions
  shown.
- When every change in the batch has every risk signal clear, the gate passes itself, recorded as
  its own reply kind (`reply=auto`), never as the person's approve, so the retrospective's stops
  and review counts stay true. Any signal on any change stops the batch for the person, naming the
  change and the signal.
- A conflict is resolved by an agent that may edit, and the resolution is reviewed again before
  it is landed; a resolution that fails its gate or review stops that change and leaves the rest
  of the batch to land.
- **Moves O6:** a batch of factory changes lands with one stop, or none when every change is
  clear, and escapes no more often than a change landed by hand.
- **Moves O3:** the ship and close gates a factory change costs fall from two per change to one
  per batch.

## Affected

- **Area:** `plugins/factory/`, the ship and close paths in `scripts/sdlc.py`, and
  `scripts/metrics.py`.
- **Files & components:** a new `plugins/factory/skills/land/`; `factory.py` (the batch, the risk
  signals, the conflict step); `sdlc.py`'s `cmd_base()`, `cmd_ship()` and `cmd_close()`, which
  `land` drives without their WAITs; `metrics.py` (`reply=auto`, `GATES`, `REQUIRED` for a landed
  batch); `AGENTS.md`, README, the factory README.
- **Downstream:** every host with `sdlc-factory`: their `main` and their remote get commits pushed
  with one approval, or none; their retrospectives read the new reply kind. `/sdlc:ship` and
  `/sdlc:close` stay as they are for changes built by hand.
- **Contracts:** a skill's WAIT (what it approves, or when); only the named steps push (`_push()`,
  behind a question that names it); close only fast-forwards and never forces;
  `disable-model-invocation` on every skill; nothing lost (O2): a conflict resolution must never
  drop either side's work; agents that judge have no Write, only the builder edits; `accept` only
  under a prompt.

## Constraints

- The push is never forced, and a refused push stops the batch before anything further lands; the
  changes already landed stay landed, as close's `push_failed` does today.
- A resolution is reviewed like the change was: an edit made after the review is never landed
  unreviewed.
- `reply=auto` is never counted as the person's approve, and any risk signal reaching the batch
  keeps the gate the person's.
- `checks.md`'s `accept` still runs under a prompt: a change with acceptance checks can't pass a
  gate by itself.
- Close's refusals still refuse: a dirty main checkout, a moved `main` or an unmerged branch stops
  that change, never forces it.
- Built-by-hand changes are untouched: `/sdlc:ship` and `/sdlc:close` work as today.

## Open questions

- ~~Does the real supervised run (seed 2026-11-17-7) come first? Seed 2026-11-10-1's own stage 1
  asks for one factory-built change closed here before any gate passes itself.~~ Resolved: no; auto-pass is on from the start, as the person chose (spec R3, R4).
- ~~Who resolves a conflict: the builder session of the change being landed (the only editor, with
  its context), or a new agent? And which reviewers check the resolution: the change's full round,
  or one round at the light depth?~~ Resolved: the change's builder session, resumed; then one round of every reviewer at the change's depth, verified (R6).
- ~~One `/sdlc:ship`-style review per change inside the batch, or the factory's own rounds standing
  in for ship's? Ship's review is today the person's independent check on the factory.~~ Resolved: the factory's rounds stand in; no `Sdlc-Findings` on a landed factory change (R5, R7).
- ~~How `land` runs ship and close without their WAITs: new `sdlc.py` entry points that take the
  batch's one approval, or `--yes` flags, and how that squares with `disable-model-invocation`,
  since `land` can't invoke `/sdlc:ship`?~~ Resolved: `factory.py` runs its own version's `sdlc.py` (`base`, `ship`, `close`), each non-interactive already; land's own WAIT is the batch's, and it invokes no skill (R1, R5).
- ~~The risk signals, exactly: the seed's list, plus "no conflict resolved", "no acceptance checks",
  "no Pre-existing finding"? And where they live: `factory.py`, or `sdlc.py`'s `preflight`?~~ Resolved: the seed's list with acceptance checks, a public issue, a resolved conflict and `land.auto` added, in `factory.py land-check` over `preflight`'s risk (R3).
- ~~The batch's limits: the most changes in one, its cost cap (agent runs per batch, as `max_runs`
  caps a run), and what a half-landed batch reports.~~ Resolved: `land.batch` (default 5); a refusal stops that change and the rest, reported as landed, stopped and not reached (R2, R5).
- ~~Prompt injection: issue text filed from the public reaching a batch that lands and pushes
  unattended. Does a change whose intent came through `/sdlc:triage` keep the gate?~~ Resolved: a non-empty `closes:` is a risk signal, so such a change always keeps the gate (R3).
- ~~Does `land` run inside the supervisor's session (busy while it lands) or as a background step
  like the agents?~~ Resolved: a session of its own in the main checkout (R2).
