---
id: 081
slug: reaches-claude-settings
tier: 1
impact: none
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
fixes: [2026-11-17-12]
serves: none
---

# 081 — Close's reaches names a change to .claude/ settings

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The review of 079-enable-factory found this ([bug] 2026-11-17-12): `landing_reach()`
(`scripts/sdlc.py:4348`) sorts a change's paths into `scripts`, `skills`, `agents` and `hosts`,
and classifies no `.claude/` path. 079's only effect was `.claude/settings.json`'s
`enabledPlugins`, so `_reaches()` returned None and close said the landed change asked nothing of
open sessions, when every session open on this clone needed `/reload-plugins` (or a restart) to
load the factory. The person was told "nothing to do" when there was something to do.

## Outcome

- `landing_reach([".claude/settings.json"])` returns a new key naming the file, so a change like
  079 gets a `reaches` that isn't None.
- `test_landing_reach_sorts_paths_into_what_each_needs` has a case for it.
- Close's report tells the person what those files ask of their open sessions, from one line in
  `skills/close/SKILL.md` beside the others.

## Affected

- **Area:** close's landing report in the plugin's own repo (`_reaches()`, `landing_reach()`).
- **Files & components:** `scripts/sdlc.py` (`landing_reach()`), `skills/close/SKILL.md` (the
  `reaches` paragraph), `tests/test_archive.py`, AGENTS.md's Closing paragraph naming what
  `reaches` covers.
- **Downstream:** the person closing a change here, and their other sessions. `cases`' scope
  (`sdlc.py:2552`) reads only `landing_reach()`'s `skills`, so a new key leaves it alone. Hosts
  never see `reaches`.
- **Contracts:** none; a new key beside the others, the existing ones unchanged.

## Constraints

- `reaches` never refuses a close, and `unknown` keeps its meaning.
- No existing key is renamed or changes meaning; the skill's "say nothing when the report has
  none" still holds.

## Open questions

- ~~Which `.claude/` paths count: `settings.json` surely; `.claude/CLAUDE.md` (read at session
  start), a project's `.claude/agents/` or `.claude/skills/`? `settings.local.json` is never
  committed.~~ Resolved: `.claude/settings.json` alone. The repo tracks only it and `CLAUDE.md`,
  which imports AGENTS.md, which nearly every change edits: counting it would make the line noise.
- ~~Does `/reload-plugins` pick up every setting, or do some (`permissions`) apply live and others
  (`enabledPlugins`) only after a reload or a restart? The answer decides the line's wording.~~
  Resolved: the line says `/reload-plugins` when `enabledPlugins` moved, and a new session for
  anything else that must take effect now.
- ~~The key's name: `settings`, or `session` for anything read when a session starts?~~ Resolved:
  `settings`, a list of paths like `hosts`.

## Approach

A branch in `landing_reach()` for the `.claude/` paths a session reads when it starts, collected
sorted under the new key; a parametrized case in `tests/test_archive.py`; one line in close's
`reaches` paragraph saying what reloading covers, and the key named in AGENTS.md's Closing
paragraph.
