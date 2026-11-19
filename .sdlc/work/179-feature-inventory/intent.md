---
id: 179
slug: feature-inventory
tier: 2
impact: minor
stage: shipped
created: 2026-11-19
opened: 2026-11-19T07:58Z
updated: 2026-11-19
shipped: 2026-11-19
idea: [2026-10-25-3, 2026-10-25-1]
depends_on:
serves: [O5]
---

# 179 — A map of what the plugin offers, and how much of it is used

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The scorecard's Simplicity pillar (S5) needs an inventory of what exists, to say what share of it
is used: "retro lists every skill, command and config key with its use in the window, setup's
footprint and the surface's growth per release, unused for N windows a retire candidate, its list
the feature map." Neither the inventory nor its words exist.

Idea 2026-10-25-3: "One docs/FEATURES.md that maps every user-facing feature a host gets — skills
and commands, the stages and gates, the board and its components (columns, cards, step track,
drawer), the tracking documents (intent, spec, plan, decisions, findings, notes, the register, the
direction and product docs), the trailers and the retro's metrics — each with a one-line definition
in the plugin's standard vocabulary (…change, tier, stage, gate, WAIT, stop, seed, nit, finding,
impact, landed, retro, direction, outcome, drift…), where it's specified, and which features it
depends on, drawn as a Mermaid graph GitHub renders. A test fails when a term the code fixes
(STAGES, tiers, impacts, nit costs and values, review passes, skills) has no entry."

Idea 2026-10-25-1: "A map of the change loop (intent → spec → plan → build → ship → close), the
release loop (release → publish) and the retro loop: each stage's gates, the `sdlc.py` calls, the
checks (gate, acceptance checks, review passes) and what it writes. Mermaid in the repo
(`docs/PROCESS.md`, rendered by GitHub), with a test that fails when a stage, skill or WAIT is
missing from it… Decide whether hosts get a copy from setup."

## Outcome

- `docs/FEATURES.md` maps every feature with its definition, where it is specified and what it
  depends on.
- `docs/PROCESS.md` maps the three loops in the feature map's words.
- Tests fail when a term the code fixes, or a stage, skill or WAIT, is missing from them.
- `retro`'s JSON gains the Simplicity figures:
  - each skill, command and config key with its use in the window, from the `Sdlc-Tool` and
    `Sdlc-Calls` trailers;
  - the share of the surface used;
  - setup's footprint in a host;
  - the surface's growth per release;
  - each item unused for N windows as a retire candidate.
- **Moves O5:** a feature nobody uses is named, so the plugin can stay small.

## Affected

- **Area:** docs, tests and the retrospective.
- **Files & components:** `docs/FEATURES.md` and `docs/PROCESS.md` (new), their tests,
  `scripts/retro.py`, `docs/REFERENCE.md` (*Retrospectives*), README.md's pointer to them,
  `docs/RETRO-SCORECARD.md`.
- **Downstream:** readers of the docs; a host's retrospective; setup, if hosts get a copy.
- **Contracts:** every term the code fixes gets one definition; the docs keys in
  `.sdlc/config.toml`, if hosts get a copy through setup (then `sdlc.py record`).

## Constraints

- The inventory is built from the code, never kept by hand, so it can't drift from what exists.
- The maps render on GitHub as they stand; no generated HTML is committed.

## Open questions

- ~~Is the inventory `retro` counts read from `docs/FEATURES.md`, or built from the code and checked
  against it?~~ Resolved: built from the code, and FEATURES.md checked against it (spec R2, R11).
- ~~What is N, the windows unused before an item is a retire candidate?~~ Resolved: 3 measured windows (spec R8).
- ~~Do hosts get a copy of either map from setup?~~ Resolved: no.
