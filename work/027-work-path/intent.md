---
id: 027
slug: work-path
tier: 2
impact:
stage: build
created: 2026-10-26
updated: 2026-10-26
idea: 2026-10-25-20
depends_on:
serves: [O1]
---

# 027 — Keep the change folders under .sdlc/

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`work/` sits at a host's root, beside its own code, so adopting the plugin adds a top-level folder
the host never asked for: the first thing a reviewer of the setup commit asks about, in a host that
keeps its root tidy. Everything else the plugin keeps is already under `.sdlc/`. The path is
`work_dir()`'s alone on disk, but `work/` is also written literally across the script's git
pathspecs, messages and regexes, `metrics.py`'s markers, `factory.py`, the skills, the defaults,
the templates and the docs; and six readers find a change's checkout as `path.parent.parent`,
which only holds while the folder sits one level below the root. Uninstall removes every file git
tracks under `.sdlc/`, so the folder can't simply be moved there either.

## Outcome

- `.sdlc/work/` is the one change folder: `new` scaffolds `.sdlc/work/NNN-slug/`, the register is
  `.sdlc/work/inbox.md`, and every reader and writer, on disk and in git, uses it.
- `/sdlc:setup` moves an existing host's `work/` there once, in a commit of its own, behind its one
  WAIT, refused while any change is open.
- Until it has, a host on `work/` is told so: `status` and `check` say to run `/sdlc:setup`, and
  every command that writes refuses. That guard and the move are a shim, removed in 1.4.0.
- Uninstall never removes `.sdlc/work/`.
- No configurable path and no support for moving it again: if a host ever needs one, it is designed
  then, and history from the move on sits at one path, so nothing has to be carried back.
- **Moves O1:** setting up a new repo adds no top-level folder, and its first closed change lives
  under `.sdlc/work/`.

## Affected

- **Area:** where the plugin keeps its change folders, and everything that names them.
- **Files & components:** `scripts/sdlc.py` (`work_dir()`, every `work/` git path and message,
  the six `path.parent.parent` lookups, `work_ignored()`, `uninstall_plan`, setup's move, the guard,
  `.sdlc/deprecations.toml`); `scripts/metrics.py`; `plugins/factory/scripts/factory.py`; the
  skills and the factory's agents and skills; `defaults/`; `templates/`; `docs/REFERENCE.md`,
  `README.md`, AGENTS.md, `docs/CONTRIBUTING.md`; tests across the suite (about 270 lines name
  `work`).
- **Downstream:** every host: where its artifacts live, its `.gitignore` check, the paths in its
  tracker issues, and its open changes, which must close before it moves. This repo too, once 027
  closes.
- **Contracts:** the change folder committed, one per branch, found only by `change_dirs()`;
  numbering never hands out a number twice; uninstall removes only what setup wrote and refuses
  while a change is live; a shim has an entry in `.sdlc/deprecations.toml` and release refuses a
  version still carrying it; `test_nothing_local`.

## Constraints

- No host moves unasked, and none with an open change.
- The move loses no file: one `git mv`, one commit, nothing rewritten.
- Accepted on purpose: readers of history look only at `.sdlc/work/`, so for changes closed before a
  host's move, release, retro and `bugs --introduced` no longer find their intents. Release and
  retro first, then move, so no window spans it. The plugin is used only in the author's own
  projects, so no outside host is affected.
- The register's ids keep counting across the move: no id is handed out twice.

## Open questions

- ~~Does setup's move carry the register's history for `next_entry_ids()` (it reads every commit
  that touched the register), or is a reused id on the day of the move accepted?~~ Resolved:
  `next_entry_ids()` reads the register's history at both paths, a fixed pathspec kept for good
  (spec R7).
- ~~Does the guard treat a repo with both `work/` and `.sdlc/work/` as half-moved, and what does it
  say?~~ Resolved: yes, a message of its own naming both folders (R6).
- ~~Does the move commit carry a marker (`Move work to .sdlc/work`) that anything reads, or is it
  only for people?~~ Resolved: its subject is for people; nothing reads it.
