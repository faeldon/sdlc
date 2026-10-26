---
id: 028
slug: remove-1-4-shims
tier: 2
impact: minor
stage: shipped
created: 2026-10-26
updated: 2026-10-26
shipped: 2026-10-26
idea:
depends_on:
serves: none
---

# 028 — Remove the 1.4.0 shims

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`.sdlc/deprecations.toml` registers four shims due in 1.4.0, and `/sdlc:release` refuses to cut
1.4.0 while they remain, with 027 (minor) already waiting in Unreleased. Each keeps code alive for
a host shape that no longer exists, since every host has been migrated:

- **`ideas-register`**: `register_path()` and `template_path()` fall back to `work/ideas.md` and
  `.sdlc/templates/ideas.md`, and every reader and writer of the register goes through that
  fallback; drift knows the old template's name.
- **`bare-date-entries`**: `ENTRY_RE`'s optional `-n` lets `[2026-10-01]` stand as an entry with
  no id; `inbox_migration()` and `cmd_migrate_inbox()` exist to give them ids (and to fold an old
  `nits.md`, the `OLD_NIT_*` regexes).
- **`retired-target-stops`**: `RETIRED_KEYS`'s `metrics.target_stops`.
- **`seed-tag-retag`**: `_is_old_seed()`, which the migration uses to retag `[seed]` as `[idea]`.

The skills and docs carry them too: `/sdlc:setup`'s `migrate-inbox` step and its `allowed-tools`
rule, the "or `ideas.md` in a repo setup hasn't moved over yet" lines in `bug`, `ship` and `retro`,
and AGENTS.md's and `docs/REFERENCE.md`'s "until 1.4.0".

## Outcome

- `sdlc.py release --check` lists no 1.4.0 shim; `status`'s Unreleased shows only
  `work-folder-move` (1.5.0).
- The four entries are gone from `.sdlc/deprecations.toml`, with the four tests that kept them.
- `register_path`'s and `template_path`'s fallbacks, `inbox_migration`, `cmd_migrate_inbox` and the
  `migrate-inbox` subcommand, `_is_old_seed`, the `OLD_NIT_*` constants and the readiness `inbox`
  item are gone; `ENTRY_RE` requires the count.
- No skill, default, template or doc names `ideas.md` as a live register or `migrate-inbox`;
  `./check.sh` is green.

## Affected

- **Area:** the register (`inbox_entries`, `register_path`), setup's readiness, drift,
  `RETIRED_KEYS`.
- **Files & components:** `scripts/sdlc.py`, `.sdlc/deprecations.toml`, `skills/setup`, `bug`,
  `ship`, `retro`, `AGENTS.md`, `docs/REFERENCE.md`, `tests/test_inbox.py`,
  `test_setup_lifecycle.py`, `test_skills.py`.
- **Downstream:** host repos on 1.4.0. All are migrated already (no `ideas.md`, bare-date entries,
  `[seed]` retags or `target_stops` left). This repo's register is already `work/inbox.md` with
  ids.
- **Contracts:** the shim/deprecation rule (`cmd_release` refuses a version still carrying one);
  "a path kept for good is not a shim", so these stay: reading `[seed]` as an idea,
  `next_entry_ids()` reading `ideas.md`/`inbox.md` in history at both folder names, titles in
  references (`ref_matches`); the `allowed-tools` rule tests (every rule used, every command
  ruled); `TEMPLATE_READS` and drift.

## Constraints

- Ids are never handed out twice: `next_entry_ids()` keeps counting every `ideas.md` history ever
  held.
- `[seed]` is still read as an idea; old intents and entries name it.
- The `work-folder-move` shim and setup's `move-work` step are untouched; it is now first in
  setup's Step 5 with nothing after it.
- `stamp_shipped` and frontmatter handling are untouched.

## Open questions

- ~~`RETIRED_KEYS`'s own comment says "Add to it, never prune it: a host can be several releases
  behind", while `deprecations.toml` says `target_stops` goes in 1.4.0. Which wins: prune the
  entry, or keep the table entry for good and drop only its shim registration?~~ Resolved: prune
  it; AGENTS.md calls a `RETIRED_KEYS` entry a shim, so the comment is the stale text, and drift
  still reports the key as unknown (spec R5).
- ~~After this, a stray `ideas.md` or an id-less heading is silently not an entry. Should `check`
  name it in one line, kept for good as a reader of what's on disk, or is silence fine given every
  host is migrated?~~ Resolved: silence, a clean slate; the both-registers problem goes too (R4).
- ~~Does readiness's `inbox` item go entirely, or stay as an `ok` line naming the register?~~
  Resolved: it goes; it can no longer warn (R3).
