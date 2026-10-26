---
id: 028
slug: remove-1-4-shims
kind: plan
created: 2026-10-26
updated: 2026-10-26
---

# 028 — Remove the 1.4.0 shims · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `ENTRY_RE` requires the count; `OLD_HEADING_RE` (new, for good) for
  `_seed_title`; `register_path`/`template_path` lose the `ideas.md` fallback; `analyze()` loses
  the both-registers problem; `next_entry_ids` reads only `inbox.md` on disk (history unchanged);
  `drift` loses the `renamed` template branch; `OLD_NIT_*`, `OLD_NITS`, `inbox_migration`,
  `_is_old_seed`, `_old_nits`, `cmd_migrate_inbox`, the subcommand, its usage line and
  readiness's `inbox` item go; `RETIRED_KEYS` becomes `{}` with a corrected comment; dead
  `e["id"]` guards simplified.
- `.sdlc/deprecations.toml`: the four 1.4.0 entries go.
- `skills/setup/SKILL.md`: the `migrate-inbox` rule, Step 3's inbox bullet, Step 5's command.
- `skills/bug`, `ship`, `retro`: the `ideas.md` clause; `skills/intent`: the before-ids clause.
- `AGENTS.md` (inbox paragraph), `docs/REFERENCE.md` (target_stops note, `ideas.md`,
  `migrate-inbox`, bare-date passages).
- `tests/test_inbox.py`: shim tests and the migrate section replaced/removed; new not-an-entry and
  register tests.
- `tests/test_adoption.py`: the old-registers adoption test goes.
- `tests/test_setup_lifecycle.py`: the target_stops test rewritten to `unknown`.
- `tests/test_sdlc.py`, `test_retro.py`, `test_bugs.py`, `test_nits.py`: register fixtures with
  bare-date headings get ids (an `idea:` holding an old heading stays).
- `tests/test_skills.py`: no shipped text names `migrate-inbox`.

## Work order

1. The register and entry ids (R1, R2, R4, R6), with the fixtures moved to ids.
2. `migrate-inbox` and readiness's `inbox` item go (R3).
3. `RETIRED_KEYS` pruned (R5).
4. Deprecations, skills and docs (R7, R8).

Each step ends with `./check.sh` green and a commit on the branch.

## Tests

- R1: `ideas.md` alone yields no entries; `config`'s `work.register` names `inbox.md`; a host
  `templates/ideas.md` is not the inbox template.
- R2: a bare-date heading is not an entry;
  `test_a_seed_shipped_by_an_idea_holding_its_heading_reads_shipped` and
  `ref_matches("[2026-10-01] [seed] Keep drafts", …)` still pass.
- R3: `main(["migrate-inbox"])` exits 2; readiness has no `inbox` item.
- R4: covered by R1's test (no `register` problem with both files).
- R5: a host setting `metrics.target_stops` is in drift's `report` as `unknown`, not `breaking`.
- R6: the existing register-ids-across-the-move test.
- R7: `status` Unreleased lists only `work-folder-move` (manual).
- R8: the no-`migrate-inbox` text test; the allowed-tools tests.
- R9: `./check.sh`.

## Rollback

`git revert` of the change's commit restores everything; nothing is written outside the repo. A
host that ran 1.4.0 meanwhile has nothing to undo, since no host file is rewritten.
