---
id: 081
slug: reaches-claude-settings
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 081 — Close's reaches names a change to .claude/ settings · plan

## Context

Bug 2026-11-17-12, found by 079's review. `landing_reach()` (`scripts/sdlc.py:4348`) has no case
for `.claude/`. So 079, which only changed `.claude/settings.json`'s `enabledPlugins`, got no
`reaches` at all, and close told the person that open sessions needed nothing. In fact they
needed `/reload-plugins` to load the factory.

## Decisions (the intent's open questions)

- **Which paths:** `.claude/settings.json` only. The repo tracks just two files under `.claude/`:
  that one and `.claude/CLAUDE.md`. `CLAUDE.md` only imports AGENTS.md, which nearly every change
  edits, and a stale copy in an open session is guidance, not behaviour. Counting it would turn
  the line into noise on every close. `settings.local.json` is never committed.
- **Key name:** `settings`, holding the list of paths, the same shape as `hosts`.
- **What the person is told:** the shared settings are read when a session starts. So
  `/reload-plugins` in each open session when `enabledPlugins` moved, and a new session for
  anything else that has to take effect now. Between stages, as for skills.

## Changes

1. `scripts/sdlc.py` `landing_reach()`: add
   `elif path == ".claude/settings.json": settings.append(path)`, add it to `found`
   (`"settings": sorted(settings)`), and add a clause to the docstring.
2. `tests/test_archive.py` `test_landing_reach_sorts_paths_into_what_each_needs`: add cases
   `([".claude/settings.json"], {"settings": [".claude/settings.json"]})` and
   `([".claude/CLAUDE.md"], {})`.
3. `skills/close/SKILL.md`, the `reaches` paragraph: add the `settings` line described above.
4. Docs that list what `reaches` covers: AGENTS.md's Closing paragraph ("shared settings at a
   new session or `/reload-plugins`"), and `docs/CONTRIBUTING.md`, with a table row for
   `.claude/settings.json` and the "Close's report lists" sentence.
5. Ship deletes the bug entry through `fixes:`, so nothing is done to it by hand.

## Verification

- `uv run --group dev pytest -q tests/test_archive.py -k reach`
- `./check.sh` (the full gate, including the skills tests on close's edited SKILL.md)
- `uv run --quiet --script scripts/sdlc.py cases` for the scope: close's skill is touched, so ship
  will name `run-cases` for it.
