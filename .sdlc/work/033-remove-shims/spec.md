---
id: 033
slug: remove-shims
kind: spec
created: 2026-10-27
updated: 2026-10-27
---

# 033 — Remove the work-folder-move and process-guide-split shims · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `.sdlc/deprecations.toml` keeps its header comment and no `[[shim]]`. `sdlc.py
   unreleased` lists no shim, so `/sdlc:release --version 1.5.0` no longer refuses on one. Test:
   `unreleased` on this repo reports no shim.
2. **R2.** `work_rel()` returns `.sdlc/work` with no fallback. These go:
   - `_OLD_HISTORY` and `old_folder()`;
   - `cmd_move_work` and `MOVE_SUBJECT`;
   - the `move-work` parser entry, its dispatch and its docstring line;
   - the readiness `work moved` item and status's `work_move`.

   Test: a repo whose history holds only `work/` resolves to `.sdlc/work`, and `sdlc.py
   move-work` exits as an invalid choice.
3. **R3.** Readers of history keep both names for good. `CHANGE_FOLDERS` and `next_entry_ids()`
   read the old folder through a constant named for history (`HISTORY_WORK = "work"`).
   `next_id()` keeps seeding from `Close`/`Drop` subjects. `test_no_literal_work_path_in_the_script`
   allows that one constant. Tests: an id held only in an old `work/inbox.md` commit is never
   handed out again, and `next_id()` after old `Close` commits is one past them.
4. **R4.** `plugins/factory/scripts/factory.py`'s `work_rel()` returns `.sdlc/work`, with no
   fallback. Its tests follow.
5. **R5.** There's no `full` layout:
   - `doc_layout()` goes, and `doc_path()` gives the process and review docs `layout: "answers"`
     with the guide, always;
   - `answers_for()`, `cmd_answers()`, the `answers` parser and dispatch, and `"answers"` in
     `READ_ONLY` go;
   - the readiness `migrate:` item goes;
   - `cmd_record` writes `layout: answers` for both docs every time, and its `--answers` flag
     goes;
   - `drift()` loses its whole-copy path for them.

   Test: a host doc with no record reads as answers with its guide.
6. **R6.** `skills/setup/SKILL.md` loses the move step, the migration step and their rules
   (`answers`, `move-work`), and calls `record` without `--answers`. Every `test_skills.py`
   invariant holds.
7. **R7.** This repo's `.claude/settings.json` drops its `answers` rule.
8. **R8.** The docs say the old forms are no longer read:
   - **AGENTS.md:** the change folder paragraph (no fallback; history keeps both names; this repo
     has moved), the guide-layout line, and the shims paragraph where it names these;
   - **`docs/REFERENCE.md`:** the whole-copy section and the move section;
   - **README.md:** the before-1.5.0 note.

   A host still on `work/` moves it by hand with `git mv work .sdlc/work`. A host holding a whole
   copy runs `/sdlc:setup reset process` (and `review`) and carries its answers over.
9. **R9.** Tests for the removed code go: `test_work_folder.py`'s move tests,
   `test_setup_lifecycle.py`'s answers and migrate tests, and the related cases in
   `test_config_resolution.py`, `test_adoption.py` and `test_skills.py`. Kept code keeps its tests.
10. **R10.** Nits `2026-10-26-12` and `2026-10-27-9` are retired at ship as moot.
11. **R11.** `./check.sh` passes, `sdlc.py drift` on this repo reports nothing, and `sdlc.py
    record` leaves `.sdlc/setup.json` unchanged.

## Design

**Deletion, with two constants renamed for what they are.** `WORK` stays the folder. The old name
survives only where history is read, as `HISTORY_WORK`, so `test_no_literal_work_path_in_the_script`
can tell a reader of history from a stale fallback.

**The layout.** Every process and review doc is answers, read after the plugin's guide. The record
keeps `layout: answers` so `setup.json` stays as it is and older plugin copies reading it still
agree.

**No detector.** A readiness warning for a leftover `work/` or a whole copy would only exist for
hosts from before 1.5.0, which makes it a shim under another name. The docs give the one-command
way out instead.

## Contracts touched

- **AGENTS.md, the change folder paragraph:** its "until 1.5.0" fallback is what goes. "Readers of
  history look only where the folder is now" changes, because history readers keep both names
  (R3). That's a policy edit, made in R8.
- **Shims:** each entry here is removed with its code, which is the contract. Nothing is left that
  would need a new entry, since R5's `layout` value isn't a config key.
- **`test_no_literal_work_path_in_the_script`:** it stays, with `HISTORY_WORK` as its one
  allowance.
- **Ids never repeat:** R3 keeps every source `next_id()` and `next_entry_ids()` count.
- **Narrow `allowed-tools`:** setup loses two rules along with the commands they cover.

## Alternatives rejected

- **Keeping `process-guide-split` until 1.6.0:** declined, so no compatibility code ships in 1.5.0.
- **A readiness detector for old hosts:** that's a shim under another name.
- **Dropping `layout` from the record:** that churns every `setup.json` for no reader's benefit.
- **Removing the stale `answers` rule from hosts' settings at uninstall:** uninstall removes only
  the current `ALLOW_RULES`, so a host that allowed `answers` keeps that inert rule. It's harmless,
  since the command no longer exists.

## Verification

- `./check.sh` green.
- `uv run --script scripts/sdlc.py unreleased` lists no shim.
- `sdlc.py move-work` and `sdlc.py answers process` each exit as an invalid choice.
- `sdlc.py drift` reports nothing, and `git diff .sdlc/setup.json` after `sdlc.py record` is empty.
