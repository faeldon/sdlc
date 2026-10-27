---
id: 033
slug: remove-shims
kind: plan
created: 2026-10-27
updated: 2026-10-27
---

# 033 — Remove the work-folder-move and process-guide-split shims · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `work_rel()` without its fallback; `OLD_WORK` → `HISTORY_WORK`, read only
  by history; `old_folder()`, `cmd_move_work`, `move-work`, the `work moved` item and status's
  `work_move` deleted; `doc_layout()`, `answers_for()`, `cmd_answers()`, `answers` and the
  readiness migrate item deleted; `doc_path()`, `cmd_record` (no `--answers`) and `drift()`
  always treat the process and review docs as answers.
- `plugins/factory/scripts/factory.py`: `work_rel()` returns `.sdlc/work`.
- `skills/setup/SKILL.md`: the move step, the migration and their two rules go; `record` loses
  `--answers`.
- `.claude/settings.json`: the `answers` rule goes.
- `.sdlc/deprecations.toml`: both `[[shim]]` blocks go.
- `AGENTS.md`, `docs/REFERENCE.md`, `README.md`: the old forms are no longer read, and how a host
  still on one moves by hand.
- `tests/test_work_folder.py`, `tests/test_adoption.py`, `tests/test_setup_lifecycle.py`,
  `tests/test_config_resolution.py`, `tests/test_readiness.py`, `tests/test_skills.py`: removed
  code's tests go, kept code's follow, and new ones pin `work_rel()` and history's ids.

## Work order

1. **The old folder** in `sdlc.py` (R2, R3), and the factory's `work_rel()` (R4).
2. **The guide layout** in `sdlc.py` (R5): `doc_path()`, `cmd_record`, `drift()`, readiness.
3. **Tests** for both, until `pytest` is green.
4. **Setup skill and settings** (R6, R7); `test_skills.py` follows.
5. **Deprecations and docs** (R1, R8).
6. `./check.sh`; `record` leaves `.sdlc/setup.json` unchanged; `drift` is clean (R11).

## Tests

- **R1:** `unreleased` lists no shim (test_deprecations reads this repo's file through release's
  refusal; manual check below).
- **R2:** a repo whose history holds only `work/` resolves to `.sdlc/work`; `move-work` is an
  invalid choice.
- **R3:** an id only in an old `work/inbox.md` commit is never handed out again;
  `test_no_literal_work_path_in_the_script` stays green.
- **R4:** the factory's tests, on `.sdlc/work`.
- **R5:** a process doc with no record reads as answers with its guide; record always writes
  answers for process and review; the answers-drift test keeps its guide-changed note.
- **R6:** `test_skills.py`'s invariants.
- **R9, R11:** the full suite and `./check.sh`.
- **Manual:** `sdlc.py unreleased` lists no shim; `sdlc.py move-work` and `sdlc.py answers
  process` exit as invalid choices; `sdlc.py record && git diff --exit-code .sdlc/setup.json`;
  `sdlc.py drift` reports nothing.

## Rollback

`git revert <sha>` of the ship commit restores both shims and their tests. It doesn't cover a host
that ran 1.5.0 meanwhile: one that moved `work/` by hand or reset its docs keeps the new layout,
which the restored code reads as well.
