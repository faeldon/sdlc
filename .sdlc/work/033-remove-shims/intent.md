---
id: 033
slug: remove-shims
tier: 2
impact: minor
stage: shipped
created: 2026-10-27
updated: 2026-10-27
shipped: 2026-10-27
idea:
depends_on:
serves: none
---

# 033 — Remove the work-folder-move and process-guide-split shims

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`.sdlc/deprecations.toml` carries two shims. `work-folder-move` (`remove_in = "1.5.0"`) keeps a
host's old top-level `work/` folder readable:

- `OLD_WORK` and the history fallback in `work_rel()`;
- `old_folder()`, `cmd_move_work` and the readiness `work moved` item;
- the factory's own `work_rel()` in `plugins/factory/scripts/factory.py`;
- setup's move step.

`/sdlc:release` refuses to cut 1.5.0 while that shim is there, and 030, 031 and 032 are waiting
to go out as 1.5.0.

`process-guide-split` (`remove_in = "1.6.0"`) cuts a host's full copy of the process and review
guides down to the host's own answers:

- `answers_for()` and `cmd_answers()` with the `answers` subcommand;
- the `full` layout in `doc_layout()`/`doc_path()`, `cmd_record` and drift;
- the readiness migrate item and setup's migration.

It landed in 032 and no release has carried it yet. The owner wants both gone now, so the plugin
carries no compatibility code into 1.5.0.

## Outcome

- `.sdlc/deprecations.toml` holds no `[[shim]]` entries, and `/sdlc:release --version 1.5.0` no
  longer refuses on a shim.
- **No old change folder:** there is no `OLD_WORK`, `old_folder()`, `move-work` subcommand or
  `work moved` readiness item, and setup has no move step. `work_rel()` always gives
  `.sdlc/work`, and so does the factory's.
- **No migration:** there is no `answers` subcommand or `answers_for()`, no `full` layout and no
  readiness migrate item, and setup has no migration. A host's process and review docs are always
  read as answers to the plugin's guide.
- **What stays, as the deprecation entries say:**
  - reading history at both folder names in `next_entry_ids()` and `CHANGE_FOLDERS`;
  - `doc_layout()`'s answers default;
  - `severities()`;
  - drift's guide-changed note.
- Each shim's named test is gone or rewritten for the code that stays, and `./check.sh` passes.

## Affected

- **Area:** `scripts/sdlc.py` (folder resolution, setup's record, drift and readiness), the
  factory's script, the setup skill, the docs.
- **Files & components:** `scripts/sdlc.py`, `plugins/factory/scripts/factory.py`,
  `skills/setup/SKILL.md`, `.sdlc/deprecations.toml`, `tests/test_work_folder.py`,
  `tests/test_setup_lifecycle.py`, any tests and readiness tests reading `work/` or
  `layout: full`, and AGENTS.md (its paragraph on the change folder's path), `docs/REFERENCE.md`
  and README.md where they describe the move or the migration.
- **Downstream:** every host on the plugin.
  - One still on top-level `work/` stops having its changes found. `work_rel()` gives
    `.sdlc/work`, and `new` starts a second numbering place beside the old folder.
  - Every host set up before 032 holds a full copy of `SDLC.md` and `REVIEW.md`. With no
    migration, the plugin reads each one as the host's answers on top of the guide it now reads in
    place, so every rule shows up twice and nothing cuts the copy back.
  - This repo has moved and has migrated, so it's unaffected.
- **Contracts:** AGENTS.md's paragraph on the change folder's path, which says `work_rel()` falls
  back to the old `work` "until 1.5.0"; the shims section ("A shim in `sdlc.py` gets an entry in
  `.sdlc/deprecations.toml`"); and the setup record's `layout` key (`drift()`,
  `TEMPLATE_READS`/`RETIRED_KEYS` if a record key retires).

## Constraints

- Readers of history keep reading both folder names for good (`next_entry_ids()`,
  `CHANGE_FOLDERS`): a repo's `Close` and `Drop` commits from before the move still count.
- Ids never repeat: removing `OLD_WORK` must not let `next_id()` miss numbers that only the old
  folder's history holds.
- Nothing else in the release changes meaning; this is deletion and the tests that follow it.

## Open questions

- ~~What exactly does the post-032 code do with a full-copy `SDLC.md` once the `full` layout is
  gone?~~ Resolved: `doc_path()` gives the guide plus the whole copy, so skills read every rule
  twice; drift proposes nothing and readiness says `ok`. The docs name `/sdlc:setup reset
  process` (and `review`) as the way out (spec R8).
- ~~What does a host still on `work/` see in 1.5.0?~~ Resolved: silence. `work_rel()` gives
  `.sdlc/work`; ids stay safe, since `next_id()` reads `.sdlc/last-id` and history's subjects. The
  docs give `git mv work .sdlc/work` (spec R3, R8).
- ~~Do the release notes for 1.5.0 tell hosts to run `/sdlc:setup` on 1.4.x first?~~ Resolved:
  `/sdlc:release`'s to say, with no changelog configured; this change writes the README and
  REFERENCE text it points to (spec R8).
- ~~Does `setup.json` keep a `layout` key?~~ Resolved: yes, always `answers`. It's a record key,
  not a config key, so no `RETIRED_KEYS` entry (spec R5, R11).
