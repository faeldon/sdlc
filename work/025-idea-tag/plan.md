---
id: 025
slug: idea-tag
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 025 — Tag ideas [idea], and call every inbox entry a seed · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

The reader already treats every tag but `bug`/`nit`/`building` as an idea (`is_bug`, `is_nit`,
`is_building`; retro's count) and `_seed_title()` strips any tag, so no reading logic changes.

- `scripts/sdlc.py`: `NEXT_RULES`' last rule `seed` → `idea` and `next_up()`'s label; `retro()`'s
  `ideas` → `{"open", "oldest"}`; `inbox_migration()` lists the `[seed]` retag and
  `cmd_migrate_inbox()` does it in its fence-aware heading loop, reporting `retagged`; comments and
  docstrings where "seed" means the idea kind say "idea". Milestone/series wording, `_seed_title`,
  `_seed_lines` and ship's "removed seed" message stay (umbrella use).
- `.sdlc/deprecations.toml`: `[[shim]] seed-tag-retag`, `remove_in = "1.4.0"`, its test.
- `templates/inbox.md`: the note opens with the concept (every entry a seed, its tag its kind:
  `[idea]`, `[bug]`, `[nit]`; `[building]`; `[seed]` reads as `[idea]`), heading form `[idea]`.
- `skills/intent`, `ship`, `retro`, `bug`, `status` `SKILL.md`: write `[idea]`, name the rule
  `idea`, read `ideas.open`; no `allowed-tools` change.
- `defaults/SDLC.md` and `.sdlc/SDLC.md`: the definition where the inbox is introduced, and "idea"
  where only the kind is meant; then `sdlc.py record` (`.sdlc/setup.json`).
- `docs/REFERENCE.md`: heading form, the definition, rule 5, `[seed]` read as `[idea]`, the retag.
- `AGENTS.md`: one clause in "The inbox".
- `work/inbox.md`: retagged by `migrate-inbox`.
- Tests: `test_defaults.py`, `test_next_up.py`, `test_retro.py`, `test_inbox.py`, `test_sdlc.py`,
  `test_adoption.py`.

## Work order

1. Script: status rule, retro key, the retag in `inbox_migration`/`cmd_migrate_inbox`, comments.
   Update the tests that pin the old names, add the retag test and the R2 tests; pytest green.
2. Deprecations entry; `test_deprecations` green.
3. Template note, then `test_defaults` (R1, R6 tests).
4. Skills, defaults + mirror, REFERENCE, AGENTS; `sdlc.py record`; `./check.sh` green.
5. `sdlc.py migrate-inbox` in the worktree (inbox clean first); rerun after ship's rebase onto
   `main` brings in `2026-10-25-23`.

## Tests

- R1: `test_defaults.py::test_the_inbox_template_shows_the_heading_the_script_reads` reads the
  `[idea]` form; new `test_the_inbox_note_defines_seed_and_its_kinds`.
- R2: `[seed]`/`[idea]` parametrized: `test_next_up.py` (rule `idea`, milestone's first grouped
  entry), `test_retro.py::test_open_changes_and_seeds_are_counted` (`{"open": 2, …}`),
  `test_sdlc.py` (ship deletes an `[idea]` entry by `idea:`).
- R3: `test_next_up.py`'s rule names `idea`.
- R4: `test_retro.py`'s `ideas` expectations.
- R5: new `test_inbox.py::test_migrate_retags_seed_entries_as_ideas` (`[seed]`, `[Seed]`, fenced
  example, `[bug]`, `[building]`; only live seeds retagged, the rest byte-identical, readiness
  `warn` → `ok`, rerun a no-op); `test_migrate_moves…` and `test_adoption.py` expect `[idea]`.
- R6: new `test_defaults.py::test_no_shipped_text_writes_a_seed_heading`.
- R7: review. R8: existing `idea:`/`[building]`/ship tests unchanged. R9: `grep -c '\] \[seed\]'
  work/inbox.md` is 0. R10: `./check.sh`, `sdlc.py drift` empty.

## Rollback

`git revert <sha>` undoes the code, docs and this repo's retag. It does not undo a host's inbox
retagged by `migrate-inbox`; that needs nothing, since `[idea]` reads as an idea under the old code
too (any tag but `bug`/`nit`/`building` does). Status and retro output names revert with the code.
