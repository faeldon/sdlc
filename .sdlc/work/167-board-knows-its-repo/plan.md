---
id: 167
slug: board-knows-its-repo
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 167 — The board knows which repo it shows, and when a landing runs unattended · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/board.py`: `_repo_id(home)`, `repo_id` in `state()`; `_is_board()` becomes
  `_board_on()` returning the parsed payload, and `cmd_board()` decides already / other repo /
  something else from it; `TRAIN_RUN_LOCK` (a copy of `landing.py`'s), `_release(fd)` (the
  factory's `_unlock()`), `train_run_held(home)`, and `_mark_unattended()`, called by `state()`, setting each landing progress's
  `unattended` (probing only while a train card isn't stopped); `_land_progress()` returns
  `"unattended": False`. Docstring gains both. Reuses `sdlc.main_root`, `sdlc._git`,
  `sdlc._try_lock`; `sdlc.py` itself is untouched (a running board keeps its old `sdlc.py`).
- `scripts/board.html`: `progressRow()` adds the `running unattended` meta line on `p.unattended`.
- `skills/dashboard/SKILL.md`: Step 1's paragraph on the first output line (R6); the bash block
  and `allowed-tools` stay.
- `tests/test_board.py`: the tests R1–R13 name; `test_the_board_writes_nothing` also lists the
  git common dir.
- `docs/REFERENCE.md`, *The board*; `AGENTS.md`, *The factory* and *The board* (R14).

## Work order

1. **Repo identity (R1–R5).** Tests: id by hash, worktree = main, no path in the body; another
   repo's board refused; a board with no `repo_id` refused; the existing second-board test
   unchanged. Then `_repo_id`, `_board_on`, `cmd_board`.
2. **The run lock on the card (R7–R10, R12, R13).** Tests: held lock marks a train card
   unattended (stopped / plain cards false); `land-step.md` alone never does; reading creates and
   holds nothing; no train, no probe; the name is a pinned copy; writes-nothing over the common
   dir. Then `TRAIN_RUN_LOCK`, `_release`, `train_run_held`, the pass in `state()`.
3. **The page (R11).** Test reads `progressRow`; then the line in `board.html`.
4. **The skill (R6).** Test on Step 1's text; then the wording.
5. **Docs (R14).** Docstring, REFERENCE.md, AGENTS.md.

## Tests

- R1 `test_the_board_names_its_repo_by_id_not_by_path`
- R2, R5 `test_a_second_board_reports_the_first_and_anything_else_is_refused` (unchanged)
- R3 `test_another_repos_board_is_a_refusal`
- R4 `test_a_board_that_names_no_repo_is_a_refusal`
- R6 `test_the_dashboard_skill_offers_another_port_on_a_refusal`, plus `tests/test_skills.py`
- R7 `test_a_held_run_lock_marks_a_train_card_unattended`
- R8 `test_land_step_alone_never_claims_a_live_loop`
- R9 `test_reading_the_run_lock_creates_nothing_and_holds_nothing`
- R10 `test_no_train_no_lock_probe`
- R11 `test_the_page_says_unattended_only_from_the_lock`
- R12 `test_the_run_lock_name_is_a_pinned_copy`
- R13 `test_the_board_writes_nothing` (extended), `test_the_board_answers_three_gets_and_nothing_else`
- R14 docs: by review (prose).

## Rollback

`git revert` covers it all: the board writes nothing, and the lock is only ever read (opened
read-only, never created). A board already running keeps serving; it reloads `board.py` on the
revert.
