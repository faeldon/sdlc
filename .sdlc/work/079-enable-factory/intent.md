---
id: 079
slug: enable-factory
tier: 1
impact: none
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
serves: [O6]
---

# 079 — Enable the factory in this repo's shared settings

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The factory (`plugins/factory/`, `sdlc-factory@sdlc`) is enabled only for whoever installs it by
hand, so a session in this repo has no `/sdlc-factory:*` skills. The repo already carries a
`.sdlc/factory.toml` (its `[ui]` for the board), and seed 2026-11-17-7 asks for the first real
supervisor run from the main checkout, but nothing committed says this repo runs the factory: a
fresh clone, or any worktree session, starts without it.

`claude plugin install sdlc-factory@sdlc --scope project`, run on 2026-11-17 in the main checkout,
wrote the setting there, uncommitted: `"enabledPlugins": {"sdlc-factory@sdlc": true,
"sdlc@sdlc": true}`, with the `attribution` object moved to the top of the file, values unchanged.
An uncommitted edit on `main` makes `/sdlc:release` refuse, and can trip close's fast-forward.

## Outcome

- **Moves O6:** factory runs in this repo, seed 2026-11-17-7's first, start from a committed
  setting rather than one person's install, so G7's evidence comes from runs anyone with the repo
  can repeat.
- `.claude/settings.json` on `main` carries `enabledPlugins` with `sdlc@sdlc` and
  `sdlc-factory@sdlc` set to `true`; its `permissions.allow` rules and `attribution` object are
  unchanged.
- `claude plugin list` in a checkout of `main` shows `sdlc-factory@sdlc`, project scope, enabled.
- The main checkout is clean again: the uncommitted edit moves onto this change's branch rather
  than staying on `main`.
- `./check.sh` passes, and `sdlc.py readiness` still reports `attribution` and `permissions` ok
  (they read the file by key, `scripts/sdlc.py:7118` and `:7143–7161`).

## Affected

- **Area:** this repo's shared Claude Code settings.
- **Files & components:** `.claude/settings.json` only.
- **Downstream:** every session opened in this repo or its worktrees; anyone who clones it, whom
  Claude Code will offer both plugins from the `sdlc` marketplace; `sdlc.py`'s
  `attribution_status()` and permissions check, which parse the file; `/sdlc:uninstall`, which
  removes setup's allow rules and `attribution` object and leaves other keys alone.
- **Contracts:** *Nothing public names the agent*: the `attribution` object must stay exactly
  `ATTRIBUTION_OFF`. `.claude/settings.json` is on `[review] sensitive`, so ship reviews it deep.

## Constraints

- No change to `permissions.allow`: enabling a plugin grants none of its commands, and an allow
  rule that lets something write would make this Tier 2.
- `attribution` keeps its values; where it sits in the file doesn't matter to the readers, which go
  by key.
- Only `.claude/settings.json`: `settings.local.json` and user scope stay as they are.

## Open questions

- ~~Should the file also name the marketplace (`extraKnownMarketplaces`, pointing at
  `faeldon/sdlc`) so a fresh clone resolves `@sdlc` without `claude plugin marketplace add` first?~~
  Resolved: no. The owner's clone registers `sdlc` from its own path, and a GitHub source under the
  same name would compete with it; a contributor adds the marketplace as README.md says.
- ~~Keep the key order `install` wrote, or put `attribution` back where it was for a smaller diff?~~
  Resolved: the file's own order, `enabledPlugins` appended last, so the diff is that key alone.

## Approach

In this change's worktree, make the same `enabledPlugins` edit to `.claude/settings.json`, then put
the main checkout's copy back (`git checkout -- .claude/settings.json`) so `main` is clean, and
confirm `claude plugin list` from the worktree still shows the factory enabled. Run `./check.sh`
and `sdlc.py readiness`.
