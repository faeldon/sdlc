---
id: 075
slug: factory-dashboard
tier: 2
impact:
stage: build
created: 2026-11-17
updated: 2026-11-17
idea: [2026-10-24-3, 2026-10-24-1]
depends_on: [074]
serves: [O6, O3]
---

# 075 — A dashboard of every open change, and UI and UX reviewers

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A person sees the repo's open changes only through `/sdlc:status` in a terminal: a snapshot, text,
and apart from the factory's files. Nothing shows changes built by hand and factory runs side by
side, or which one is waiting on them.

The supervisor (070) runs several changes at once, each in its own worktree under
`.claude/worktrees/`, and the person sees them only by asking it. A run's state is spread over
every change's folder: `build/round-<N>.md`, `reviews/round-<N>/<role>.md` (each opening
`VERDICT: PASS|CHANGES`), `verified.md`'s `KEPT:`/`DROPPED:` lines, `decisions.md`, `notes.md`,
`runs/`. No one file holds it all, and nothing shows it at a glance, so which change is stuck in
rework, which has a decision waiting on them, and which is ready to ship takes reading files or a
question. The factory it learned from (zazencodes' `software-factory-claude-code-v2`,
`factory/dashboard.html`) shows this as a board: a column per stage, a card per job with a row of
verdict chips per round, a "your call" flag, cost, and a drawer that opens each file the run
wrote.

That factory also reviews what a change looks like: its `reviewer-ui` starts the app's dev server
on a port of its own, screenshots the page at desktop and phone widths, and checks the change
against the app's theme, spacing, contrast and overflow. Ours has code, security, test and
behaviour reviewers; none looks at a page, and the plugin can't tell a repo has a front end,
since nothing declares one.

## Outcome

- `/sdlc:dashboard` opens a live page of every open change in every worktree, built by hand or
  by the factory: its tier, stage, artifacts, open questions, undone notes and next command, and
  for a factory change a row of chips per round (builder report, each reviewer's verdict, verifier
  kept/dropped), open decisions in `decisions.md`, the approver's READY or ESCALATE, and time and
  cost where 074's `runs/` figures exist, with a click through to each file in its folder.
- The page and the server behind it are read-only: nothing is written for them.
- A test builds the board from fixture change folders (by hand at two tiers; a factory run with
  a `CHANGES` then a `PASS`, an open decision, a missing cost) and asserts what it serves.
- New factory agents, `reviewer-ui` and `reviewer-ux`, run in a round only when the repo declares
  a front end (a declaration whose default keeps today's runs unchanged), write
  `reviews/round-<N>/ui.md` and `ux.md` in the existing verdict shape, and their `CHANGE:` lines go
  through the verifier like any reviewer's.
- The dashboard is this repo's first UI, so the UI reviewer's first subject is the dashboard
  itself.
- **Moves O6:** a person running several factory changes sees at a glance which one needs them and
  which is ready, and stops only for those; a change with a visible surface gets a reviewer that
  looked at it.
- **Moves O3:** a person sees at a glance which open change is waiting on them, and what to run
  next, without asking status.

## Affected

- **Area:** the factory plugin (`plugins/factory/`): its mechanism, a new skill, a new agent.
- **Files & components:** `plugins/factory/scripts/factory.py` (a read-only `board` command over
  the same worktree walk `cmd_ready()` uses; the front-end declaration in `factory.toml`'s
  defaults and `cmd_config()`; the UI reviewer's place in `verdicts`' routing and `model_for()`),
  `plugins/factory/skills/dashboard/SKILL.md` (new), `plugins/factory/agents/reviewer-ui.md`
  (new), `plugins/factory/skills/build/SKILL.md` (refresh the board after each step),
  `plugins/factory/README.md`, the factory's tests.
- **Downstream:** the person running the supervisor; hosts with the factory installed, through the
  new `factory.toml` key and an agent that can start a host's dev server; `sdlc`, which reads at
  ship the files a run leaves, so the UI reviewer's file must read like the others there; and
  `_agent_sessions()`, which must see the new role's sessions in `runs/`.
- **Contracts:** the verdict file shape (`VERDICT:` then `- CHANGE:` lines), `verified.md`'s
  lines, `runs/<role>.sessions`, `factory.toml`'s existing keys, and the `Sdlc-*` trailers, all
  unchanged. 074 writes the cost figures the cards show; 072 and 073 also edit `factory.py`'s step
  routing.

## Constraints

- Read-only over change folders; the board's only write is under `.sdlc/reports/`, which ignores
  itself.
- No price table: the cost shown is 074's pass-through figure, labelled API-equivalent.
- The UI reviewer judges and doesn't edit: nothing beyond its one review file, filed as the other
  agents' are. It starts only the dev server the repo declares, on its own port, stops only the
  process it started (never by name), never signs in or submits a form, and never runs with no
  front end declared.
- `checks.md` stays the builder's and `accept`'s alone (`test_no_agent_but_the_builder_runs_checks`).
- `sdlc` loads nothing from `plugins/` (`test_sdlc_loads_nothing_from_plugins`).
- The skill holds the skill invariants: narrow `allowed-tools`, every script call via
  `uv run --quiet --script`, no `if` or loops in bash blocks.
- The Windows rules for any new write or subprocess; external scripts on the page, if any, at
  pinned versions, and self-contained is better.

## Open questions

- ~~Static or live? Does a skill that only opens a read-only page need a WAIT?~~ Resolved: live,
  a localhost server (`sdlc.py board`) the page polls, in core as `/sdlc:dashboard` so changes
  built by hand show too; no WAIT, since it writes nothing.
- ~~How does a repo declare a front end?~~ Resolved: `factory.toml`'s `[ui]` (`serve`, `paths`,
  `shoot`, …), read from the base branch's copy, unset by default.
- ~~How does the reviewer look at the page from a headless session?~~ Resolved: `factory.py
  shots` starts the declared server and runs the declared screenshot command; the reviewers only
  read the images, and a failed shot refuses the review rather than running it blind.
- ~~The UX reviewer: here or split out?~~ Resolved: built here, `reviewer-ux`, on the same shots.
- ~~Every round or only on UI paths, and which model?~~ Resolved: once the diff touches `[ui]
  paths`, kept for later rounds; in `SCALED` (sonnet at Tier 2 or full depth, haiku otherwise).
- ~~One change or two?~~ Resolved: one.
- Land's state on the cards (whether a ready change would land unasked): `land-check`'s verdict,
  computed by `factory.py` and written to no file, so core can't read it. Deferred.
