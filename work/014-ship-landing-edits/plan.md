---
id: 014
slug: ship-landing-edits
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 014 — Ship does its own landing edits · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: `cmd_ship(root, ident, leave)` gains two refusals before any write (two seeds
  titled as `idea:`; a `--leave` path already staged), then stamp → `_drop_seed()` →
  `_stage_change()`. New `_seed_title()` (strips the `IDEA_RE` prefix and a ` → …` pointer),
  `_seed_lines()`, `_drop_seed()` (edits `ideas.md` as lines), `_stage_change()` (reuses
  `_dirty_paths()`, `git add -- <paths>`). `idea` read as `load_change()` reads it. The tree is
  the folder's `git rev-parse --show-toplevel`. `ship` gains `--leave PATH` (repeatable).
- `skills/ship/SKILL.md`: Step 0 names `--leave` for paths committed apart; Step 6 no longer
  deletes the seed or builds a `git add` list, its bash block runs `ship`, `git status --short`,
  `git commit`, `sync`; `Bash(git add *)` leaves `allowed-tools`.
- `defaults/SDLC.md` and `.sdlc/SDLC.md`: the seed paragraph says `sdlc.py ship` deletes the entry
  and stages it; `.sdlc/setup.json` re-recorded.
- `tests/test_sdlc.py`: the landing-edit tests below.
- `tests/test_adoption.py`: asserts `ship` staged the code, the folder and `.sdlc/last-id`,
  instead of staging them itself.
- `docs/REFERENCE.md`: no change; it says a closed seed is deleted, which stays true.

## Work order

1. Seed matching and deletion, with their tests.
2. Staging and the staged-but-left check.
3. Wire into `cmd_ship` and argparse; the `cmd_ship` tests.
4. Ship's Step 0 and Step 6, and `allowed-tools`; `tests/test_skills.py`.
5. `tests/test_adoption.py`.
6. The process docs, `sdlc.py record`, `./check.sh`.

## Tests

- R1: `test_ship_deletes_the_seed_its_idea_names_and_nothing_else` (neighbours byte-identical),
  `test_ship_deletes_the_last_seed_without_a_trailing_blank_line`.
- R2: the same test's `idea:` forms (title, full heading, with pointer) and
  `test_ship_matches_a_heading_that_carries_a_pointer`.
- R3: `test_two_seeds_with_the_idea_s_title_refuse_before_any_write`.
- R4: `test_ship_with_no_seed_to_remove_says_so_and_ships_twice`,
  `test_ship_with_no_idea_mentions_no_seed`.
- R5, R7: `test_ship_stages_the_change_and_leaves_what_it_is_told_to` (a path with a space,
  `.sdlc/last-id`, `--leave`, HEAD unchanged).
- R6: `test_a_left_path_already_staged_refuses_before_any_write`.
- R8: `tests/test_skills.py` (every command a rule, every rule used).
- R9: `tests/test_adoption.py`.
- R10: `sdlc.py drift` clean in the gate.
- Manual: this change's own ship, where `sdlc.py ship 014` removes the `[building]` seed and
  prints what it staged.

## Rollback

`git revert <sha>`. A host that shipped with this script had its seed removed and paths staged
inside its own approved commit, so there is nothing outside it to undo.
