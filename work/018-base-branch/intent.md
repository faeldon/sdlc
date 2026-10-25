---
id: 018
slug: base-branch
tier: 2
impact: minor
stage: shipped
created: 2026-10-25
updated: 2026-10-25
shipped: 2026-10-25
idea:
depends_on:
serves: [O1]
---

# 018 — Let a host name its base branch

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A host whose default branch is `master` can't run a change through the plugin. Its first
`/sdlc:intent` stopped partway: `new --worktree` opened GitHub issue #11, then created no
worktree, branch or `work/` folder, so the issue is left open with no change behind it. The
reporter:

> The plugin assumes the base branch is called main, and this repo's is master. `sdlc new` takes
> a `--base master` option, so I could finish creating the change. But that would only get past
> this first step: ship rebases onto main; close and release refuse unless the main checkout is on
> main; the commit history and release logs are read from main. None of those can be changed in
> config, so the change would get stuck at ship or close.

`scripts/sdlc.py` hardcodes `main` in about twenty places: `cmd_new`'s and `context`'s `--base`
defaults, `cmd_base`'s `rebase main` and `merge --ff-only main`, close's on-`main` check,
`--is-ancestor … main` and `rev-parse main`, `closed_changes()`'s and retro's
`log --first-parent main`, release's and publish's branch checks, `tag --merged main` and
`rev-parse main`, and the `{base}..main` spans. The skills say "off main" in their prose and their
questions. `--base` reaches only `new`, so a host that uses it ends up with a change it can't
ship.

## Outcome

- A host whose base branch isn't `main` can take a change from `/sdlc:intent` to `/sdlc:close`,
  then `/sdlc:release` and `/sdlc:publish`, with no flags.
- Every place the script means "the base branch" reads it from one resolved value, so none can
  disagree. `test_adoption.py` proves it by running new→close in a scratch repo whose only branch
  is `master`.
- A host on `main` sees no difference, and needs no config line.
- **Moves O1:** a repo whose default branch is `master` (or anything else) reaches its first
  closed change. Today it can't, and it never gets past ship.

## Affected

- **Area:** `scripts/sdlc.py` (config resolution and every git call that names `main`), the
  skills that say "main" to the person, `docs/REFERENCE.md` (the new key), and setup if it should
  detect the branch.
- **Files & components:** `load_config()` / `cmd_config`, `cmd_new`, `cmd_base`, `cmd_close` and
  `_handoff`, `closed_changes()`, `unreleased()`, `cmd_release`, `cmd_publish`, `retro()`,
  `context`, `changed_paths` callers; `skills/{intent,ship,close,drop,release,publish,retro,status,setup}/SKILL.md`;
  `RETIRED_KEYS` / `TEMPLATE_READS` / `drift` if the key needs a record entry; tests.
- **Downstream:** every host running the plugin. Hosts on `main` must behave exactly as now.
  Hosts on another branch are blocked today, including the one that reported this, which has
  issue #11 left open.
- **Contracts:** "Only publish pushes" (publish's push target changes, and its push mustn't
  widen). Close only fast-forwards, and `closed_changes()` walks the base branch's first-parent
  line. Numbering never falls back between schemes, which matters for the orphaned issue.

## Constraints

- No behaviour change for a host on `main`, whether its config sets the key or not.
- Read in one place, `load_config()`. No command guesses the branch on its own.
- Never merge the base into a change branch, and never stash. `cmd_base`'s rules stay as they
  are, with only the branch name changed.
- The skills' bash rules must still match exactly. If a skill needs the branch name, it gets it
  from `config`, not from a shell variable that `allowed-tools` can't cover.

## Open questions

- ~~Is it a config key (e.g. `git.base`) that setup fills in, or worked out from `origin/HEAD` /
  `init.defaultBranch` with config as an override? Should setup ask, or detect and show?~~
  Resolved: `[git] base`, detected from `main` and then `origin/HEAD` when unset; setup offers to
  pin a detected non-`main` base (spec R1, R11).
- ~~Why is #11 still open?~~ Resolved: it isn't. `new` failed with "fatal: invalid reference:
  main" and closed #11 as not planned. But it printed only the failure and the `opened` line, never
  the close, so its output reads as if the issue were open. Fixed by refusing before the claim (R3)
  and reporting the drop's outcome (R4).
- ~~What should the reporting host do about #11?~~ Resolved: close it by hand. There's no option to
  adopt an issue (spec, Alternatives rejected).
- ~~Can `.sdlc/setup.json` / `drift` stay unchanged for a new key?~~ Resolved: no entry. A key added
  isn't one retired.
- ~~Should the skills name the branch from `config`?~~ Resolved: yes, from `git.base` (R10).
