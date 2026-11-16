---
id: 066
slug: retro-report
tier: 2
impact: minor
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-10-24-4
depends_on:
serves: [O4]
---

# 066 — A retro report and process views from each change's numbers

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`/sdlc:close` writes every change's numbers onto its `Close` commit as `Sdlc-*` trailers (elapsed,
agent and waiting time, stops against what was required, tokens, rework, fixes), and nothing turns
them into something a person reads. `sdlc.py retro` folds them into a `metrics` block of medians
for the retro skill to reason over; its findings then live only in that session's conversation and
the direction doc's prose. The figures behind a decision ("stops ran over target", "review caught
most of this") are never written down where the next retrospective, or the person, can check them.

This session closed eight changes, three of them at once across two sessions (063, 064, 065), and
each close printed its numbers: 062 spent 36 minutes waiting on the person against 27 of agent
time; 064 stopped the person 9 times against 5 required. No view says how many changes one person
can run at once before cycle time rises, or how waiting time compares with agent time across a
window: the capacity question this session raised can't be answered from what the plugin keeps.

The process guide keeps "no dashboard" for these signals ("things to notice, not things to stare
at"), so the answer is a report, not a dashboard. Raised 2026-10-24.

## Outcome

- Each retrospective commits a report the script fills from history, with no model tokens, beside
  the direction doc: the window's process views, roughly the DORA set: cycle time (a change's
  intent to its close), throughput (changes closed per week, by tier), rework (060's declared
  rework and its questions), escapes (bugs reported against changes), waiting time against agent
  time, work in progress (changes open at once), and capacity (cycle time beside how many changes
  ran at once). No single velocity figure.
- The report is rendered from a template in `templates/`, overridable in `.sdlc/templates/` like
  every file the plugin writes, and its figures match `sdlc.py retro`'s; a test renders it from a
  fixture's history.
- The retro skill's process pass cites the report's figures, so its findings name a number the
  report holds.
- **Moves O4:** each retrospective's process findings cite a figure from the committed report
  (cycle time, waiting against agent time, capacity), not a recollection, and the report is there
  for the person to read without asking.

## Affected

- **Area:** the retrospective loop's output and what it commits.
- **Files & components:** `scripts/sdlc.py` (the views, computed from closed changes' trailers and
  history; rendering the report; `cmd_retro_commit`'s allowed paths); `templates/` (a new report
  template) and `TEMPLATE_READS`; `skills/retro/SKILL.md`; `tests/test_retro.py`,
  `tests/test_defaults.py` (the template's shape); `docs/REFERENCE.md`, `AGENTS.md`.
- **Downstream:** every host's retrospective (one more file committed); hosts that override
  templates; `drift`/`setup` through `TEMPLATE_READS`. `templates/` is irreversible: a template
  once shipped is in hosts' hands.
- **Contracts:** metrics trailers are a contract, read and never redefined; `retro-commit` writes
  only what a retrospective owns; the one shape for shipped docs (`tests/test_defaults.py`);
  `metrics.py` and `indicators.py` stay pure; "no dashboard" in the process guide; retro's output
  size (059): no per-change blob.

## Constraints

- No model tokens for the report: the script fills it; the retro skill reads its figures rather
  than recomputing them.
- No single velocity figure, and no dashboard.
- A window where `measure` couldn't read transcripts (`Sdlc-Coverage: none`) says so in the
  report, never fills in zeros.
- `retro-commit` still refuses anything a retrospective doesn't own; the report is one path added,
  by name.

## Open questions

- ~~Where does the report live: a committed path such as `.sdlc/retros/<date>.md` (`.sdlc/reports/`
  ignores itself), or inside the direction doc?~~ Resolved: `.sdlc/retros/<date>.md`, written by
  `retro-commit` itself at commit time.
- ~~Which views are worth their measuring: is capacity (cycle time against changes at once) meaningful
  with so few changes per window?~~ Resolved: kept, every row showing the changes it rests on; a
  span is close time minus `elapsed`, so nothing new is measured.
- ~~Does the report replace `metrics` in `retro`'s output, or render from it?~~ Resolved: neither;
  a new `process` block that the report renders, `metrics` kept for the skill's passes.
- ~~Is the template a host doc `drift` refreshes, or a plain template a host overrides?~~ Resolved: a
  plain template, `templates/retro.md`, overridable in `.sdlc/templates/`.
- ~~Does the retro skill read only the report, or still `metrics` for what the report leaves out?~~
  Resolved: it reads `process` from `retro`'s JSON, the report's figures, and `metrics` as before.
