---
id: 067
slug: sync-title-and-worktree-main
tier: 1
impact: minor
stage: shipped
created: 2026-11-16
updated: 2026-11-16
shipped: 2026-11-16
idea: 2026-10-25-8
depends_on:
serves: none
---

# 067 — Close the small gaps in sync and worktree setup

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

A host raised two gaps on 2026-10-25:

- **The issue keeps its first title.** `sdlc.py sync` rewrites a change's issue body from its
  artifacts, but never its title. The GitHub tracker's `sync()` (`scripts/trackers/github.py:572`)
  runs `gh issue edit --body-file -` and nothing more. A change whose `# NNN — Title` heading is
  reworded at spec, or after the person edits the intent, leaves its issue under the title `new`
  opened it with. Anyone reading the tracker sees the old name until close archives it, and even
  then the title stays.
- **`worktree_setup` can't name the main checkout.** `commands.worktree_setup` gets `{worktree}`,
  the new worktree's path, but nothing for the main checkout it runs from. A host whose setup links
  untracked data from the main checkout into the worktree has to rebuild that path itself, by
  parsing `git rev-parse --git-common-dir`. Every host with that need writes the same shell, in a
  config value.

## Outcome

- After the intent's heading is retitled, `sdlc.py sync NNN` sets the issue's title to match, says
  so in `done` (`title`), and leaves an unchanged title alone, with no extra `gh` call. A test with
  the fake `gh` checks both.
- `commands.worktree_setup` can use `{main}`, filled with the main checkout's path wherever
  `{worktree}` is filled. `docs/REFERENCE.md` and the config comment name it. A command without
  `{main}` behaves as it does today.
- `./check.sh` passes.

## Affected

- **Area:** the GitHub tracker's sync, and the intent skill's worktree-setup step.
- **Files & components:** `scripts/trackers/github.py` (`sync()`), and the dict
  `_tracker_change()` in `scripts/sdlc.py` hands it, if the title isn't already in it. Also
  `skills/intent/SKILL.md` Step 5 (`{main}` beside `{worktree}`), `docs/REFERENCE.md` (the
  `worktree_setup` placeholders), the config default's comment in `scripts/sdlc.py`, and tests.
- **Downstream:** every host on the GitHub tracker sees its issue titles kept current, and hosts
  with a `worktree_setup` can use the new placeholder. `scripts/trackers/` is in
  `[review] sensitive`.
- **Contracts:** a tracker never reads `.sdlc/`, so the title arrives in the dict core hands it.
  `trackers/command.py` gets the same dict and keeps working whether or not it reads the new key.
  Only the named steps push, and this adds no push.

## Constraints

- `sync` never creates an issue, and never touches one close has archived (closed, or labelled
  `landed`). Retitling follows the same rule.
- A failed title edit must not undo the body edit, nor be reported as success.
- `{main}` is filled by the skill, as `{worktree}` is. No script starts running the host's command.

## Open questions

- ~~Which title does the issue take: the heading exactly as written (`063 — Close warns…`), or
  the title alone, the way `new` creates it? Whatever `new` uses should win, so a retitled issue
  looks like a fresh one.~~ Resolved: the title alone, the heading with `TITLE_ID_RE`'s id
  stripped, as `new` gives `claim()`.
- ~~Does close's `archive()` set the title too, for a change retitled after its last sync, or is
  `sync` enough, since ship syncs right before close?~~ Resolved: `sync` is enough. Ship syncs
  after its commit, and a shipped change can't be retitled before close.
- ~~Does the command tracker (`trackers/command.py`) get the title in its dict, and should its docs
  say so?~~ Resolved: it gets the same dict, but it has no sync ("at close only"), so nothing in it
  changes.

## Approach

Hand the tracker the change's current title in the dict `_tracker_change()` builds, if it isn't
there already. In `github.py`'s `sync()`, after the body edit, compare it with the issue's title
and run `gh issue edit --title` only when they differ, adding `title` to `done`. In the intent
skill's Step 5, replace `{main}` with the main checkout's path where `{worktree}` is replaced, and
name `{main}` in `docs/REFERENCE.md` and the config comment. Tests: a retitled change's sync edits
the title, and an unchanged one doesn't. The skill text and reference name `{main}`. It takes in
seed `2026-10-25-8`.
