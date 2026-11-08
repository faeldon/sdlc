---
id: 044
slug: status-ranks-the-backlog
kind: plan
created: 2026-11-08
updated: 2026-11-08
---

# 044 — Status ranks and groups the backlog, so choosing the next change takes one read · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`:
  - `BODY_KEYS` gains `Priority`
  - `PRIORITIES`, `entry_priority()`, `entry_theme()`
  - `analyze()` reports bad `Priority:` lines (kind `priority`)
  - `NEXT_RULES` gains `priority` and `low`, and `NEXT_SHOWN = 10`
  - `next_up()` splits `ready` by priority and adds `id`, `kind`, `theme`, `themes`, `waiting`, `all`
  - `last_touched()` and `QUIET_HOURS`; `cmd_status` sets `touched` and `quiet` on each open change
  - `print_status` prints the touched mark, ten lines, the `Themes:` block, the waiting count and `--all`
  - the `status` subparser gains `--all`
- `tests/test_next_up.py`: tests for R1–R7 and R11; the five-line test becomes ten.
- `skills/status/SKILL.md`: Step 1 describes the new Next up; Step 3's precedence follows R8.
- `skills/idea/SKILL.md`, `skills/bug/SKILL.md`: `Theme:` and optional `Priority:` in the draft.
- `skills/triage/SKILL.md`: keeps either line on the entries it files.
- `templates/inbox.md`: the note names the two optional lines.
- `docs/REFERENCE.md` (**What comes next**), `README.md`: the new order, ten lines, themes and `--all`.

## Work order

1. Entry readers: `Priority` key, `entry_priority`, `entry_theme`, the `check` problem. Test R1.
2. `next_up()` ranking, themes, waiting and all. Tests R2, R3, R5 (data), R6 (data), R11.
3. Printing and `--all`. Tests R4, R5, R6.
4. `last_touched`, `quiet` and the open-change mark. Test R7.
5. Skills, template and docs (R8–R10); `tests/test_skills.py` and `tests/test_defaults.py` pass.
6. The amendment (R12–R14): `THEMELESS_NUDGE` and `next_up()`'s `themeless` count with its
   status line; `/sdlc:idea --themes` in `skills/idea/SKILL.md` (Step 2's section, Step 3's table,
   Step 4's question, Step 5's edit), and its note in `skills/bug/SKILL.md`.
7. `./check.sh`.

## Tests

- **R1:** `test_priority_reads_high_med_low_and_reports_a_bad_word` (also checks a nit's Priority).
- **R2:** `test_priority_high_ranks_first_and_low_last`.
- **R3, R5:** `test_themes_count_every_open_entry_by_kind_best_ranked_first`.
- **R4:** `test_status_prints_ten_then_counts_the_rest`.
- **R6:** `test_status_all_lists_every_candidate_once_by_theme`.
- **R7:** `test_open_change_shows_when_it_was_last_touched`.
- **R11:** `test_next_up_orders_by_rule` is unchanged, with every item's `theme` None.
- **R12:** `test_status_points_at_the_themes_pass_from_five_themeless`.
- **R13:** `tests/test_skills.py` (one WAIT, every command covered). Manual: `/sdlc:idea --themes`
  from the main checkout after the merge, then `status`.
- **R14:** `test_inbox_commit_records_a_themes_pass_as_one_update`.
- **R8–R10:** `tests/test_skills.py` and `tests/test_defaults.py` pass. Manual: `status` and `status --all` from this worktree.

## Rollback

`git revert` of the change's commit undoes all of it. Nothing outside the repo is written. A host
whose entries gained `Priority:` or `Theme:` lines keeps them, and the reverted code ignores them,
since body keys it doesn't know are read as text.
