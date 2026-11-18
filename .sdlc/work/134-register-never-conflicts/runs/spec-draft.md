---
id: 134
slug: register-never-conflicts
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 134 — The register never conflicts when a change lands · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. A change's branch never edits the register.** After `sdlc.py ship` (by hand) or `factory.py land` (factory), the change's commit leaves `.sdlc/work/inbox.md` exactly as it was at the branch's base. `test_ship_leaves_the_register_as_the_base_has_it` and `test_a_landing_leaves_the_register_as_the_base_has_it` fail if the commit's diff names the register.
2. **R2. New entries are held in the change's folder.** Every entry ship or a landing would have added (carried seeds, filed bugs, nits, a seed split off from an issue on `closes:`) is written, whole and in the register's own entry format, to `.sdlc/work/NNN-slug/entries.md`, and is committed with the change. `test_a_landing_holds_its_carried_seeds_bugs_and_nits` fails if any of them shows up in the register on the branch, or is missing from `entries.md`.
3. **R3. Retired nits are held too.** Each nit a change retires is a `Retire <id>: <reason>` line in `entries.md`, before its first entry. The register's copy is never deleted on the branch. The commit message's `Retired nits:` paragraph doesn't change. `test_a_landing_retires_the_nits_its_intent_names` (rewritten) fails if the nit leaves the branch's register, or if `entries.md` has no `Retire` line for it.
4. **R4. Close files and retires in the `Close` commit.** `_close_commit()` applies the change's register changes to the main checkout's register in the same commit that removes the folder: each held entry appended, and each seed `idea:` names, each bug `fixes:` names and each `Retire` line's nit removed. All of it comes from the change's own commit (`git show <branch>:…`), and every other line stays byte for byte. `test_close_files_and_retires_in_the_close_commit` fails if any of this lands in a separate commit, or if the `Close` commit's parent stops being the change's commit (`closed_changes()`).
5. **R5. The outcome test.** Two changes, A and B, start from the same base. Each takes a seed and carries one forward. A is shipped and closed, then an idea is filed on the base through `inbox-commit`, then B is rebased (`sdlc.py base`) and closed. The rebase reports no conflict. The register holds each of the three new entries exactly once, and neither taken seed. This is `test_two_landings_and_an_idea_never_conflict_on_the_register` (hand ship) and `test_two_factory_landings_never_conflict_on_the_register` (`factory.py land`/`land --close`). Either fails on a conflict, a missing entry or a duplicate.
6. **R6. Close checks first and is safe to rerun.** Close checks `entries.md` before its merge, along with its other preconditions. It refuses on a file it can't parse, on a held id the base's register already holds with different text, and on an `idea:` title that matches two entries. A held entry the base already holds word for word is skipped. A retirement whose entry is already gone is skipped and reported (`register.gone`), not refused. `test_close_refuses_a_held_id_the_base_holds_otherwise_before_merging` fails if the merge ran. `test_a_close_rerun_files_each_entry_once` fails on a duplicate.
7. **R7. Close takes the lock for the register write.** The register is written under `_main_lock()`, the same lock `inbox-commit` takes, so an `/sdlc:idea` filed in the middle of a close keeps both. `test_close_and_inbox_commit_keep_both_entries` fails if one is lost.
8. **R8. Ids stay unique while held.** `next_entry_ids()` also counts ids found in every checkout's `entries.md` files on disk and in any commit, on any branch, that touches one. `test_next_entry_counts_the_ids_a_change_holds` fails if a held id is handed out again.
9. **R9. A held split-off seed is still the issue's record.** When `committed_only` is off, `recorded_issues()` reads every worktree's `entries.md`. Between ship and close, an issue split off as a held seed still has exactly one record. `test_a_held_split_seed_records_its_issue` fails if the issue reads as unrecorded.
10. **R10. A shipped change keeps its seed until it closes.** `_open_claims()` still counts a `shipped` change's `idea:` and `fixes:` (a `dropped` change still claims nothing), since the seed now stays on the base until close. `test_a_shipped_change_claims_its_seed_until_it_closes` replaces `test_a_shipped_change_no_longer_claims_its_seed`. It fails if `groups` or `inbox-commit` lets someone take or retire that seed before close.
11. **R11. Ship refuses an uncommitted register edit.** `sdlc.py ship` refuses, before writing anything, while the worktree has uncommitted edits to the register. The message says to move the entries to `entries.md` or file them with `/sdlc:idea`. `test_ship_refuses_an_uncommitted_register_edit` fails if it stamps.
12. **R12. Drop never loses held entries.** `sdlc.py drop` refuses while the change's `entries.md` holds an entry, since a `Drop` commit keeps the base's tree and the entries would never be filed. `test_drop_refuses_while_the_change_holds_entries` fails if it stamps.
13. **R13. Both paths write one format.** The factory writes `entries.md` with its own code and `sdlc.py` reads it with its own. Each has a copy of the other's parsing (`ENTRIES`, the `Retire` line regex), and a test pins them together. `test_the_entries_factory_holds_are_the_ones_close_files` fails if close misses or misreads anything `_dispose()` or `retire_nits()` wrote.
14. **R14. The docs agree with the code.** The ship skill (`SKILL.md`, `undone.md`, `factory.md`, `closes.md`), the land skill, REFERENCE.md (*`.sdlc/work/` and worktrees*) and AGENTS.md (*The register*, *Closing*) say where entries go and when they reach the register. No skill tells anyone to append to or delete from the register during ship. `test_no_skill_ships_an_entry_into_the_register` fails if `skills/ship/` or the land skill tells anyone to append to or delete from `.sdlc/work/inbox.md` during ship.

## Design

### What I checked in the code

- **Where the conflict comes from.** `_dispose()` (factory.py) appends to the worktree's register, and `retire_nits()` deletes from it after `sdlc.py ship`. `cmd_ship()` deletes the `idea:` seed and the `fixes:` bugs with `_drop_seed()`. The ship skill's Step 6 appends nits, bugs and carried seeds by hand. All of it rides the change's commit, which `sdlc.py base` then rebases onto a base whose register has also grown at the end.
- **Close fast-forwards.** `cmd_close()` merges with `--ff-only`. `closed_changes()` and factory's `closes()` read a `Close` commit's first parent as the change's commit. So a separate register commit between the two would break both. Putting the register write inside the `Close` commit doesn't.
- **A shipped change can't be dropped.** `cmd_drop()` refuses `stage: shipped`. Once ship has committed, the change either closes or nothing happens, so entries held in its folder always reach the base through close.
- **Ids.** `next_entry_ids()` scans every checkout's register on disk and `git log --all -p` over the register paths. Neither finds an `entries.md`, hence R8.
- **Intake.** `recorded_issues()` reads every checkout's register for `Issue:` lines. The seed closes.md splits off must stay readable, hence R9. `mark_issues()` already runs after `_close_commit()` with `committed_only=True`, so it reads the entries the `Close` commit filed.
- **`fix_trailers()`** reads a bug's severity from the newest commit on the branch that still has the entry. With nothing deleted on the branch, the branch tip has it.
- **`_open_claims()`** skips `shipped` only because ship used to delete the seed (its docstring says so), hence R10.

### `entries.md`

It lives in the change's folder, is committed with the change, and is removed from the base along with the folder. History keeps it. Every path to it is built from `work_rel()`. Its shape:

- A `# NNN-slug — entries` title line.
- Then any number of `Retire <id>: <reason>` lines, one per retired nit.
- Then the entries, each exactly as it will appear in the register (`## [<id>] [<tag>] <title>` and its body).

`parse_entries()` reads it unchanged. No template is added, because the plugin writes this file and a host doesn't shape it. Seeds and bugs the change takes are not listed: close reads them from `idea:` and `fixes:` in the change's own `intent.md`, so there is one record of them.

### Writers

- **Factory `_dispose()`.** Appends to `entries.md` instead of the register. `filed_nit()`'s rerun check reads `entries.md`. The register-template check is dropped, because nothing creates the register at landing any more.
- **Factory `retire_nits()`.** Adds `Retire` lines, skipping ids already there, and the landing stages `entries.md` instead of `INBOX`. `cmd_land`'s `_commit_failed()` branch reads the retired nits from `entries.md`'s `Retire` lines instead of comparing `HEAD:INBOX`.
- **Ship skill Step 6.** Writes the approved entries and `Retire` lines to `entries.md` with `Write`/`Edit` (it already has both), and the "Write is for those files only" list gains it. `undone.md`, `factory.md` and `closes.md` point at the same file. Ids still come from the one `next-entry` call. `preflight --question`'s wording doesn't change: "the nits shown recorded in .sdlc/work/inbox.md" is still what happens, at close.
- **`sdlc.py ship`.** Stops calling `_drop_seed()`. It keeps its check, against the worktree's register, that a title names only one seed. It gains R11's refusal and prints what close will retire. `ship <NNN>` keeps its name and flags.

### Close

Before the merge, `cmd_close()` reads `entries.md` and `intent.md` from the branch, builds the planned register text from the main checkout's register (`_splice_entries()` for appends, the span logic of `_entry_spans()`/`_drop_seed()` for removals, `_seed_lines()`'s matching for `idea:`), and adds R6's refusals to `report["refusals"]`. `--check` shows the plan as `report["register"] = {"file": [...], "retire": [...], "gone": [...]}`.

In `remove_folder()`, under `_main_lock()`, `_close_commit()` reads the register again (an `inbox-commit` may have landed in the meantime), rebuilds the same plan, writes it, and runs `git add` on it along with the `git rm -r` of the folder in the one `Close` commit. If the commit fails, the register is put back the same way the folder already is. A rerun that finds the folder gone has nothing to do, because the register went in the same commit. A dropped change's close is unchanged (R12 makes sure it holds nothing).

### Edge cases

- **A landing that commits and stops before close** (the intent's second question). The entries are held on the branch and filed when close runs. The ids in the commit message resolve on the base from then on. The base never shows an entry from a change that hasn't landed.
- **A branch from before this change.** Its commit still edits the register, rebases as before, and is settled by `resolve`'s existing register rule (`conflict.md`; factory `cmd_resolve()`'s `drop_entries`). Its close finds no `entries.md`, and a seed already deleted is reported `gone`. Both stay as they are.

### Boundaries

- **Always:** every new entry reaches the base's register in its change's `Close` commit, under the lock, exactly once.
- **Ask first:** nothing new. Ship's and land's existing yes approves the entries, and close's yes approves landing them.
- **Never:**
  - a register edit on a change's branch;
  - a register commit between a change's commit and its `Close`;
  - a `.gitattributes` merge driver;
  - reading the register in `measure`, release or publish;
  - a change to `preflight`'s question wording.

## Contracts touched

- **⚠ A policy edit: what a `Close` commit holds** (AGENTS.md, *`.sdlc/work/` is committed* and *Closing*). Today a `Close NNN-slug` commit only removes the folder. With this change it also files and retires the change's register entries. Two things stay true: its first parent is still the change's commit, and a rerun keyed on the folder still resolves. `retro.py` diffs the change's commit, not the `Close`. AGENTS.md is edited in this change to say so. Your call.
- **⚠ A policy edit: who commits the register** (AGENTS.md, *The register*). The rule says `inbox-commit` is the only code that commits the register *on its own*, always on the base branch in the main checkout. Close now commits it too, never on its own, always with the folder's removal, on the base in the main checkout, under the same lock. "An entry never rides on a change's branch" becomes true with no exception, which is the point. The paragraph is reworded to name close.
- **The record is committed before the issue is told** (*Intake*). `mark_issues()` still runs after `_close_commit()` and reads only committed text. Between ship and close, R9 keeps each issue with exactly one record.
- **Nothing lost, and a rerun finishes** (O2, *Closing*). Close checks everything before its merge, writes in one commit, and keys its rerun on the folder. A shipped change can't be dropped, and R12 covers a dropped one.
- **Ids from one `next-entry` call** (*The register*). Unchanged for the callers. `next_entry_ids()` widens what it counts (R8).
- **The factory never imports `sdlc.py`; each copies the other's parsing, pinned** (*The factory*). R13.
- **Release, publish and measuring never read the register** (`test_release_publish_and_measuring_never_read_the_register`). The register write is in `_close_commit()`, never in `measure_change()`.
- **Every path built from `work_rel()`; no `main` in a git call; Windows rules** (`newline="\n"`, `as_posix()`, `encoding="utf-8"`). The new code follows each of them, and the existing tests cover them.
- **Skills: narrow `allowed-tools`, one WAIT** (`tests/test_skills.py`). Ship and land run no new command and add no new question. Their changes are to prose and to `Write`/`Edit` targets.

## Alternatives rejected

- **(b) `merge=union` on the register.** In a conflicting block, union keeps both sides' lines. So when a change deletes a seed and the base edits or appends right next to it, the seed comes back with no warning (an entry written twice), and two appends can fuse into one malformed entry. It would also need a `.gitattributes` line in every host, which setup would have to write and `drift` track, and a host that never got the line would still conflict. Choice (c), doing both, adds the same risks to (a).
- **(a) as written: `inbox-commit` on the base after the change lands, in its own commit.** That commit would sit between the change's commit and its `Close` on the first-parent line, where `closed_changes()` and factory's `closes()` take the `Close`'s parent to be the change. It also leaves a gap between two commits where a stopped run has to work out which half happened. Putting the write inside the `Close` commit keeps the parent rule and makes it one step.
- **Filing entries on the base at ship time, through `inbox-commit` from the worktree.** Ship would need the main checkout clean and on the base, a new way for ship to refuse. Retiring the taken seed at ship time loses it if the landing never finishes. And the base would show entries for a change that never landed.
- **`sdlc.py ship` moving whatever the worktree register gained into `entries.md`.** It would keep the old instructions working. But it is a hidden rewrite of a file the person approved, and the factory's nit retirement happens after ship, so it would still need its own path. Writing `entries.md` directly, with R11 catching the old habit, is plainer.
- **Making `entries.md` a template under `templates/`.** Its shape is the plugin's, to be read, not the host's. A template would add a `TEMPLATE_READS` entry and an override no host needs.

## Verification

```bash
uv run --group dev pytest -q tests/test_register_lands.py tests/test_land.py tests/test_sdlc.py tests/test_bugs.py tests/test_inbox.py tests/test_groups.py tests/test_nits.py -n auto
uv run --group dev pytest -q -m portable
./check.sh
```

Healthy output:
- Every test passes, including:
  - the two outcome tests from R5;
  - the `test_ship_deletes_*` tests, rewritten as `test_close_retires_*` with the same cases (by id, by title, the last entry with no trailing blank line, a theme's several seeds, "no seed to remove" said);
  - the R13 pin.
- `check.sh` ends with ruff clean, `ruff format --check` clean, pytest green, and `claude plugin validate --strict` passing.

This change touches `skills/ship/`, which has cases, so ship requires a `Skill evals: ran, <score>` or `Skill evals: skipped, <why>` note. Running them is a paid call and the person's to decide. In this repo, close hands off to the merged script (`_handoff()`), so this change's own close runs the new code. This change's own folder was written the old way, so it holds no `entries.md`, and its close exercises the `gone` path for any seed it deleted itself.

