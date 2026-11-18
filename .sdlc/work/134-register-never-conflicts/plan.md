---
id: 134
slug: register-never-conflicts
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 134 — The register never conflicts when a change lands · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`
  - `ENTRIES = "entries.md"`, `RETIRE_LINE_RE`, and `held_entries(text)`: reads a change's
    `entries.md` into `{"retire": [(id, reason)], "entries": [...], "text": {id: chunk},
    "problems": [...]}`. Reuses `_heading_entry()`, `_entry_spans()`, `FENCE_RE`.
  - `register_plan(register, intent, held)` (new, pure): the register text close writes, built
    from `_entry_spans()`/`_drop_seed()`'s span rule for removals (`idea:` through
    `_seed_lines()`'s matching, `fixes:` by id, each `Retire` id) and `_splice_entries()`'s
    append; returns `{"text", "file", "retire", "gone", "skipped", "refusals"}`. `_drop_seed()`
    is gone with ship's deletions; its span rule is `_without_entry()`, on lines.
  - `cmd_ship()`: stops calling `_drop_seed()`; keeps the one-seed-per-title refusal; adds R11's
    refusal of an uncommitted register edit; prints what close will retire and file.
  - `_branch_register_plan()` (new): `register_plan()` with the intent and `entries.md` read from
    the branch (`git show`), so what lands is what was shipped.
  - `cmd_close()`: plans against the base's register before the merge, refuses on R6's cases
    (`register: …`), shows `report["register"]`, also under `--check`.
  - `_close_commit()`: under `_main_lock()`, re-plans against the main checkout's register on
    disk, writes it, `git add`s it with the folder's `git rm -r`, one `Close` commit; puts the
    register back on a failed step.
  - `next_entry_ids()`: also counts ids in every checkout's `*/entries.md` and in `git log --all`
    over `.sdlc/work/*/entries.md` (R8).
  - `recorded_issues()`: with `committed_only` off, also reads every checkout's change folders'
    `entries.md` (R9).
  - `_open_claims()`: a `shipped` change claims its seeds and bugs again (R10).
  - `cmd_drop()`: refuses while `entries.md` holds an entry (R12).
- `plugins/factory/scripts/factory.py`
  - `ENTRIES`, `RETIRE_RE` (copies, pinned by R13's test).
  - `_dispose()`: appends to the folder's `entries.md` (started with its `# NNN-slug — entries`
    title) instead of the register; `filed_nit()` reads that file; no template needed.
  - `retire_nits()`: writes `Retire <id>: taken in by <change>` lines into `entries.md`, skipping
    ids already there; `retired_ids()` reads them.
  - `cmd_land()`: stages nothing but what `sdlc.py ship` staged plus `entries.md`; the
    `_commit_failed()` branch takes the retired nits from `retired_ids()`.
- `skills/ship/SKILL.md`, `undone.md`, `factory.md`, `closes.md`; `plugins/factory/skills/land/SKILL.md`:
  entries and `Retire` lines go to the change's `entries.md`; close files and retires them.
- `docs/REFERENCE.md` (*`.sdlc/work/` and worktrees*), `AGENTS.md` (*The register*, *Closing*).
- Tests:
  - `tests/test_register_lands.py` (new): R1, R4–R8, R11, R12, R13, the outcome tests.
  - `tests/test_sdlc.py`: the `test_ship_deletes_*` cases rewritten as `test_close_retires_*`
    against `register_plan()`; ship now leaves the register alone.
  - `tests/test_bugs.py`: `test_ship_removes_each_bug_*` and `test_ship_deletes_an_untagged_seed_*`
    rewritten as close's.
  - `tests/test_groups.py`: `test_a_shipped_change_claims_its_seed_until_it_closes` (R10).
  - `tests/test_land.py`: `_dispose` tests read `entries.md`; the nit retirement test (R3).
  - `tests/test_intake.py`: R9.
  - `tests/test_adoption.py`: ship no longer says `removed bug`; close's `Close` commit removes it.
  - `tests/test_resolve.py`: its old-way register edit is now refused at ship (R11), moved to
    `entries.md`, and filed by close.
  - `tests/test_land.py`'s resolution fixture builds a branch landed before this change (its
    commit deleting what it took), the only kind that can still conflict on the register.
  - `tests/test_archive.py`: the split-off seed is held in `entries.md` and told at close.
  - `tests/test_skills.py`: `test_no_skill_ships_an_entry_into_the_register` (R14).

## Work order

1. **The held file and the plan.** `held_entries()`, `register_plan()`; the old ship-deletion
   cases rewritten against `register_plan()`. Nothing calls it yet; the suite stays green.
2. **Ship leaves the register alone; close applies the plan.** `cmd_ship()` loses its deletions
   and gains R11; `cmd_close()` gains its check and `_close_commit()` its write, under the lock.
   R1 (hand), R4, R6, R7, R11 tests; the bug and adoption tests move to close.
3. **The edges.** R8 `next_entry_ids()`, R9 `recorded_issues()`, R10 `_open_claims()`, R12
   `cmd_drop()`, each with its test.
4. **The factory.** `_dispose()`, `retire_nits()`, `cmd_land()` write `entries.md`; R1 (factory),
   R2, R3, R13 tests; the existing `_dispose` tests read the new file.
5. **The outcome.** R5's two tests: hand ship and factory landing, an idea filed between.
6. **The docs.** Ship and land skills, REFERENCE.md, AGENTS.md; R14's test. Then `./check.sh`.

## Tests

- R1: `test_ship_leaves_the_register_as_the_base_has_it` (`test_register_lands.py`),
  `test_a_landing_leaves_the_register_as_the_base_has_it` (`test_land.py`, with R2, R13 and the
  factory's R5, which need its landing fixtures).
- R2: `test_a_landing_holds_its_carried_seeds_bugs_and_nits`.
- R3: `test_a_landing_retires_the_nits_its_intent_names` (rewritten).
- R4: `test_close_files_and_retires_in_the_close_commit` (a real close); the `test_close_retires_*`
  cases in `test_sdlc.py` and `test_bugs.py` run the same `register_plan()` close runs, as pure
  text, rather than a close each.
- R5: `test_two_landings_and_an_idea_never_conflict_on_the_register`,
  `test_two_factory_landings_never_conflict_on_the_register`.
- R6: `test_close_refuses_a_held_id_the_base_holds_otherwise_before_merging`,
  `test_a_close_rerun_files_each_entry_once`, plus an unparseable file and an ambiguous title.
- R7: `test_close_and_inbox_commit_keep_both_entries`.
- R8: `test_next_entry_counts_the_ids_a_change_holds`.
- R9: `test_a_held_split_seed_records_its_issue`.
- R10: `test_a_shipped_change_claims_its_seed_until_it_closes`.
- R11: `test_ship_refuses_an_uncommitted_register_edit`.
- R12: `test_drop_refuses_while_the_change_holds_entries`.
- R13: `test_the_entries_factory_holds_are_the_ones_close_files`.
- R14: `test_no_skill_ships_an_entry_into_the_register`.

## Rollback

`git revert` of the change's commit undoes all of it. It doesn't undo what a `Close` commit
already filed: those entries are on the base, where they belong, and stay. A branch shipped with
this code holds an `entries.md` the reverted code never reads: before closing it under the old
code, append its entries to the register by hand (or with `/sdlc:idea`) and delete the seeds its
`idea:` and `fixes:` name, as the old ship did.
