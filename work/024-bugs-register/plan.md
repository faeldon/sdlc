---
id: 024
slug: bugs-register
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 024 — One inbox for seeds, bugs and nits · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py` — `register_path()` (the shim), `ENTRY_RE` and `inbox_entries()`, `entry_ref()`
  / `ref_matches()`, `next_entry_id()`, `nit_entries()` over `[nit]` entries, `severities()`,
  `_fix_trailers()`, retro's `bugs`; new `next-entry`, `bugs`, `bug-commit`, `migrate-inbox`.
- `scripts/metrics.py` — `parse_trailers()` keys `Sdlc-Fixes` and `Sdlc-Retired` by id.
- `templates/inbox.md` (new); `templates/ideas.md` and `templates/nits.md` removed;
  `templates/notes.md`, `templates/direction.md` wording.
- `skills/bug/SKILL.md` (new); intent, spec, ship, close, retro, status, setup, uninstall skills.
- `plugins/factory/scripts/factory.py` — its notes text names the inbox.
- `.sdlc/deprecations.toml` — the `ideas-register` shim, `remove_in = "2.0.0"`.
- `defaults/SDLC.md`, `.sdlc/SDLC.md` — the inbox, a `#### Bugs` section, nit entry lines; then
  `sdlc.py record` (`.sdlc/setup.json`).
- `README.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md`, `AGENTS.md` — docs.
- `work/ideas.md`, `work/nits.md` → `work/inbox.md`; `.sdlc/DIRECTION.md` references (migrated).
- Tests: `tests/test_inbox.py` (new), `tests/test_bugs.py` (new), `tests/test_nits.py` (ported),
  `tests/test_next_up.py`, `tests/test_retro.py`, `tests/test_sdlc.py`, `tests/test_metrics.py`,
  `tests/test_skills.py`, `tests/test_defaults.py`, `tests/test_adoption.py`.

## Work order

Seven phases, each reader in place before anything writes the new shape. Each ends with
`./check.sh` green and is committed on the branch (`Phase N: …`, the owner's identity, no agent
trailers).

Findings from the code: `GROUP_CHANGE_RE` (`sdlc.py:3846`) would read `2026` out of an unquoted id
on a `Groups:` line, so entry ids are taken first; `cmd_ship` reads `idea:` through
`frontmatter.load` (`sdlc.py:1673`), switched to `frontmatter_list()`; the never-read test
(`tests/test_nits.py:197`) is widened to the inbox and measuring.

1. **The inbox file and its shim (R1 reading, R2, R4).** `register_path(root)` (`work/inbox.md`,
   else `work/ideas.md`) behind every reader; `ENTRY_RE` (`\[(\d{4}-\d{2}-\d{2})(?:-(\d+))?\]`)
   replacing `IDEA_RE`; `inbox_entries()` with `id`, `tag` and known body lines;
   `template_path()` taking a host `ideas.md` override for `inbox.md`; `DOC_TEMPLATES`; `check`
   reports both files present; `cmd_retro_commit` allows the register's file; the
   `deprecations.toml` entry; skills, templates and docs renamed in wording only.
2. **Ids and references (R5–R8).** `entry_ref()`/`ref_matches()` in `_seed_lines`, the orphan
   check, Next up's building set, `After:` waits and warnings, `_milestone_verdicts`; `Groups:`
   ids before change ids; `next_entry_id()` over every worktree's register plus
   `git log --all -p --since=<day>`; `next-entry` in `READ_ONLY`; duplicate ids in `check`; Next up
   commands by id; intent, ship and retro write ids.
3. **Nits as entries (R9).** `nit_entries()` over `[nit]` entries, same return shape and problems;
   `templates/nits.md` removed; ship writes nit entries with ids, `Retired nits:` by id.
4. **Migration (R3).** `migrate-inbox` (refusals, `git mv`, ids, nits folded in, references
   rewritten, rerun no-op, never commits); setup offers it; run here.
5. **Bugs (R10–R14).** `severities()`; bug checks; `bugs` with `--touching`/`--introduced`;
   `■ Bugs` and the `bug` rule's severity order; `bug-commit`; `/sdlc:bug`; the process docs'
   `#### Bugs` section; `record`.
6. **The fix cycle (R15–R17).** `fixes:` read and checked; Next up exclusion; ship deletes `fixes:`
   entries byte for byte; `_fix_trailers()` in close, not on drop; `parse_trailers()`.
7. **Retro and the last docs (R18–R19).** Retro's `bugs` block and the skill's escape pass;
   `REFERENCE.md`, `README.md`; the adoption run; `record`, `drift` empty.

## Tests

- R1, R2, R4 (phase 1): `tests/test_inbox.py` — reads the inbox, falls back to `work/ideas.md`
  (`test_ideas_md_still_reads`, named in `deprecations.toml`), both present is a problem, the
  template override shim, a fenced example ignored; the widened never-read test.
- R5–R8 (phase 2): `tests/test_inbox.py` — allocation (another worktree, a same-day deleted id, a
  new date), each reference form in each reader, `Groups:` with a `2026-…` id beside a `006`,
  duplicates; `tests/test_next_up.py` command strings; `tests/test_retro.py` verdicts by id.
- R9 (phase 3): `tests/test_nits.py` ported to entries.
- R3 (phase 4): `tests/test_inbox.py` — fixture register to expected inbox, rerun no-op, shipped
  title kept, each refusal.
- R10–R14 (phase 5): `tests/test_bugs.py` — severity from the host doc and the fallback, each check
  problem, `bugs` filters, each `bug-commit` refusal and subject, Next up order, `■ Bugs`;
  `tests/test_skills.py` for `/sdlc:bug`.
- R15–R17 (phase 6): `tests/test_bugs.py` — ship byte for byte, trailer fields and `unknown`, drop
  writes none; `tests/test_metrics.py` — parse, existing keys unchanged.
- R18–R19 (phase 7): `tests/test_retro.py` — one fix, one retired, one open; `tests/test_adoption.py`
  end to end and a migration on the old layout; `test_defaults.py` mirror tests; `drift` empty.
- Manual, after phase 4: `status` from this worktree shows the same Next up as before, with id
  commands, and `check --strict` is clean.

## Rollback

`git revert` of the branch's commits on `main` restores code, templates, docs and this repo's
`work/ideas.md`, `work/nits.md` and `.sdlc/DIRECTION.md`. Not covered: a host that ran
`migrate-inbox` and went back to an older plugin, which reads neither `work/inbox.md` nor
`[2026-10-25-3]` headings: it reverts its own migration (`git mv` back, `-n` stripped). `File` and
`Retire` commits stay in history. Issue #24's body re-syncs on the next `sdlc.py sync 024`.
