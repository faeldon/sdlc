---
id: 013
slug: landing-reach
tier: 1
impact: none
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea:
depends_on:
serves: none
---

# 013 — Close says what a landed plugin change needs from open sessions and hosts

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The plugin is used from a clone (`claude plugin list` shows `Read from: <path-to-clone>`), and
several Claude Code sessions in other repos run it while changes to it land here. After a
`/sdlc:close`, nothing says which of those sessions or hosts need to do anything:

- script changes (`scripts/sdlc.py`, trackers, metrics) are live in every session the moment
  `main` moves;
- skill text (`skills/*/SKILL.md`, its `allowed-tools` included) is read when a session starts,
  so it needs `/reload-plugins` or a restart;
- what `/sdlc:setup` copied into a host (`defaults/`, `templates/`, config keys) never changes
  until setup is rerun there.

The person works this out by hand from the diff each time, or doesn't. Mixed state is the real
risk: a session halfway through `/sdlc:ship` keeps its old skill text while calling the new
script, and a renamed subcommand or flag breaks the run partway. `docs/CONTRIBUTING.md` says only
"an edit takes effect in the next session", and nothing about `/reload-plugins`, mixed state, or
when a host needs setup.

## Outcome

- In the plugin's own repo (`_own_repo()`), close's JSON report carries a `reaches` entry, built
  from the paths the landed change touched. It names which kinds changed (scripts, skills, what
  setup puts in a host), which skills, and the action for each: none for scripts,
  `/reload-plugins` at a stage boundary for skills, `/sdlc:setup` in each host for the rest.
  Tests cover a script-only change, a skill-only change, a `defaults/` change and a change with
  none of these.
- `skills/close/SKILL.md` Step 4 reports it in a line or a short list, and says nothing when it
  is empty or absent; a host's close never has it.
- `docs/CONTRIBUTING.md` gets a subsection under "Working from a clone", on open sessions after a
  change lands: the table above, the stage-boundary rule (reload between skills, never during
  one) and the after-close checklist.

## Affected

- **Area:** close (script and skill), contributor docs
- **Files & components:** `scripts/sdlc.py` (`cmd_close`'s report, a helper sorting changed paths
  into kinds), `skills/close/SKILL.md` Step 4, `docs/CONTRIBUTING.md`, `tests/test_sdlc.py`
- **Downstream:** the person developing the plugin and their open sessions in other repos. Hosts
  see nothing: the entry exists only when the repo is the plugin itself.
- **Contracts:** "Only publish pushes" and close's step order are untouched: this adds a report
  entry, not a step. Nothing messages another session.

## Constraints

- Close writes nothing new and never refuses over this: a failure working out `reaches` drops the
  entry, the way `measure` never refuses.
- The kinds come from paths, not guesses: `scripts/`, `skills/` (and `plugins/factory/skills/`),
  `defaults/`, `templates/`, and config keys (`RETIRED_KEYS`, `TEMPLATE_READS`, the config
  loader).
- Only the developer's own sessions are reached, and only through the report: no `SendMessage`,
  no hooks.

## Open questions

- ~~Does a plugin skill re-read its `SKILL.md` on each invocation, or only at session start?~~
  Resolved: the advice is `/reload-plugins` between stages, which is right either way, so it
  doesn't hang on the answer. Not tested.
- ~~How does close tell from paths that a change touched config keys?~~ Resolved: it doesn't. A
  key's rename lives in `scripts/sdlc.py` with its `RETIRED_KEYS` entry, which setup's drift
  reports as breaking; `hosts` is `defaults/` and `templates/`, and CONTRIBUTING says a key
  change needs setup too.
- ~~Are the factory's skills listed apart from `sdlc`'s?~~ Resolved: one list, by namespaced
  name (`sdlc:close`, `sdlc-factory:build`).

## Approach

A pure helper takes the changed paths and returns the kinds and skill names. `cmd_close` calls it
after `merge --ff-only`, on the diff between the old `main` and the new one, only when
`_own_repo(main)`, and adds the result as `report["reaches"]`. Close's Step 4 gets one paragraph
on reporting it; CONTRIBUTING gets the subsection. No nits taken in.
