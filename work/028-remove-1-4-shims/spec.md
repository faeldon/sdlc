---
id: 028
slug: remove-1-4-shims
kind: spec
created: 2026-10-26
updated: 2026-10-26
---

# 028 — Remove the 1.4.0 shims · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. The register is always `<work>/inbox.md`.** `register_path()` returns `work / INBOX`, with
   no `ideas.md` fallback; `template_path()` no longer reads `.sdlc/templates/ideas.md` as the
   inbox template; `drift`'s `renamed` case for it goes (it is reported like any host template
   with no plugin counterpart). Tests: a repo with only `ideas.md` has no entries, and `config`'s
   `work.register` names `inbox.md`.
2. **R2. An entry has an id.** `ENTRY_RE` requires the `-n` count, so `## [2026-10-17] [idea] x` is
   not an entry; `_heading_entry()`'s id is always a string. `_seed_title()` keeps stripping a
   bare-date prefix, for good, through its own pattern (`OLD_HEADING_RE`), since it reads `idea:`
   lines of intents in history. Tests: a bare-date heading is not an entry;
   `test_a_seed_shipped_by_an_idea_holding_its_heading_reads_shipped` still passes.
3. **R3. `migrate-inbox` is gone:** the subcommand and its usage line, `cmd_migrate_inbox`,
   `inbox_migration`, `_is_old_seed`, `_old_nits`, `OLD_NITS` and the `OLD_NIT_*` regexes, and
   readiness's `inbox` item, which can no longer warn. `[seed]` still reads as an idea (existing
   tests stay). Test: `sdlc.py migrate-inbox` exits with argparse's error.
4. **R4. `check` says nothing about old shapes** (a clean slate): the "both registers exist"
   problem goes.
5. **R5. `metrics.target_stops` leaves `RETIRED_KEYS`.** The table stays, empty, its comment
   saying an entry is a shim, registered in `.sdlc/deprecations.toml` and removed in the version
   it names. Test: a host still setting it gets `drift`'s `unknown` report ("the plugin doesn't
   read it"), replacing `test_a_host_still_setting_target_stops_is_told`.
6. **R6. Ids are never handed out twice.** `next_entry_ids()` stops reading an on-disk `ideas.md`
   in each checkout, and keeps its history pathspec over both names in both folders, for good;
   `fix_trailers()` keeps reading both names in history. The existing register-ids-across-the-move
   test still passes.
7. **R7. `.sdlc/deprecations.toml` holds only `work-folder-move`.** The four 1.4.0 entries go, with
   their four named tests (removed, or rewritten as R1–R5 say). `status`'s Unreleased lists no
   1.4.0 shim.
8. **R8. The texts stop naming them.** `skills/setup/SKILL.md` loses Step 3's inbox bullet, Step
   5's `migrate-inbox` command and its `allowed-tools` rule; `bug`, `ship`, `retro` lose "or
   `ideas.md` in a repo `/sdlc:setup` hasn't moved over yet"; `intent` loses the clause about an
   entry from before ids; AGENTS.md's inbox paragraph and `docs/REFERENCE.md` (the `target_stops`
   note, the `ideas.md`, `migrate-inbox` and bare-date passages) say what holds now. Test: no
   skill, default, template, README or REFERENCE text names `migrate-inbox`.
9. **R9. The rest of the suite stands on ids and `inbox.md`.** The migrate tests go
   (`test_inbox.py`'s migrate and refusal tests, the adoption test
   `test_a_bare_repo_moves_its_old_registers_into_the_inbox`); any fixture writing a bare-date
   heading or an `ideas.md` as the live register moves to ids and `inbox.md`. `./check.sh` is
   green.

## Design

Almost all deletion. `OLD_INBOX` stays, used only where history is read (`next_entry_ids`'
pathspec, `fix_trailers`' paths), and its comment says so. `_seed_title` gets
`OLD_HEADING_RE = ^##\s*\[\d{4}-\d{2}-\d{2}(?:-\d+)?\]\s*\[[^\]]+\]\s*(.+)$`, the one place a bare
date is still accepted, commented with why (an old `idea:` holding a whole heading).

With ids always set, the guards that only existed for a missing one are simplified where plainly
dead (`key(e)` in `cmd_retro_commit` becomes `e["id"]`; the `if e["id"]` filters in
`parse_entries`' id map, the duplicate-id check and `recorded_issues`). Nothing reading history is
touched. `config` still reports `work.register` (every skill reads it); it now always names
`inbox.md`. Setup's Step 5 keeps `move-work` as the only command in that slot.

## Contracts touched

- **Shims (`deprecations.toml`, `cmd_release`)**: each shim leaves with its entry and its test, as
  the rule asks; after this, release refuses 1.4.0 for nothing here.
- **"A path kept for good is not a shim"**: the history readers stay and get no entry: `[seed]` as
  an idea, the history pathspec in `next_entry_ids`/`fix_trailers`, `_seed_title`'s bare-date
  strip, titles in references.
- **`RETIRED_KEYS` ("a RETIRED_KEYS entry is one")**: the code comment's "never prune it"
  contradicts AGENTS.md; the policy wins and the comment is corrected, not the policy. `breaking`
  still means a key in that table.
- **Narrow `allowed-tools`**: setup's `migrate-inbox` rule leaves with its command, so
  `test_skills.py` still finds every rule used.
- **Always Tier 2**: it changes what `sdlc.py` reads in a host; every host is migrated, as the
  intent records.
- **Ids never twice (O2's invariant)**: R6.

## Alternatives rejected

- **`check` problems for a stray `ideas.md` or an id-less heading**: chosen against, for a clean
  slate; it would have been permanent code for a shape no host has.
- **Keeping `target_stops` in `RETIRED_KEYS` for good**: contradicts the shim registration and
  AGENTS.md; `drift` still reports the key as unknown.
- **Keeping `migrate-inbox` as a tool kept for good**: nothing left to migrate, and it carries a
  whole old-nits parser.
- **Requiring the count in `_seed_title` too**: retro's milestone verdicts would read seeds
  shipped from old intents as `vanished`.

## Verification

- `./check.sh`: ruff, format, pytest, `plugin validate` all pass.
- `uv run --quiet --script scripts/sdlc.py status`: Unreleased shows only
  `shim work-folder-move: remove in 1.5.0`.
- `uv run --quiet --script scripts/sdlc.py migrate-inbox`: "invalid choice".
- `grep -rn "migrate-inbox\|OLD_NIT\|_is_old_seed\|target_stops" scripts skills defaults templates
  README.md docs AGENTS.md` finds nothing beyond a history note R8 may keep in REFERENCE.
