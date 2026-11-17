---
id: 100
slug: seeds-marked-by-changes
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 100 — Open changes mark their seeds without editing the register · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `skills/intent/SKILL.md`: Step 5 sets `idea:` and stops; the `Edit` of each entry, the
  `[building]` retag and the `Building in` line go (R1). Step 0 now names `work.register` where it
  skims the register (the removed lines were the skill's one mention of the key, which
  `READS_CONFIG` requires), and the factory paragraph no longer says "the register included".
- `skills/intent/batch.md`: Step 5.3 writes the intent and its frontmatter lines only (R1).
- `scripts/sdlc.py`:
  - `next_up()` returns `building`: one item per entry being built (`id`, `title`, `kind`,
    `change`), in register order. It already computes the names from `open_changes` (`ideas_of()`
    and `fixes`); it now pairs each with `f"{id}-{slug}"`, the folder name, as the milestone code
    in the same function already does. A legacy tag nobody names gets `change: None` (R3).
  - `print_status()`: `N being built` beside `N waiting on earlier seeds`; under `--all`, each as
    `<id> <title> — NNN-slug` or `— tagged [building]` (R3).
  - `cmd_bugs()` and `_nits_report()`: each entry gains `building`, the first `_open_claims()`
    change whose ref `ref_matches()` it, else `None` (R4).
  - `_claimed_by()` (new, beside `_open_claims()`): the first claim matching an entry, shared by
    `bugs`, `nits` and `inbox-commit`'s refusal, which had the same expression inline.
  - `_open_claims()`'s and `is_building()`'s docstrings, and the comment above `ENTRY_RE`: nothing
    writes the tag now; older registers still carry it.
- `tests/test_skills.py`: R1's test; `test_intent_takes_a_theme_s_seeds_as_one_change` drops the
  `Edit` assertion.
- `tests/test_next_up.py`: R3 (`building`, status line, `--all` list).
- `tests/test_bugs.py`: R4 for bugs, R6 (ship deletes an untagged named idea, by id and title),
  R7 (drop gives it back: next_up, groups, inbox-commit), R8 (`check` quiet on an untagged named
  entry).
- `tests/test_nits.py`: R4 for nits.
- `tests/test_groups.py`: R5 (an untagged named idea is refused with the change's name), R7.
- `tests/test_resolve.py`: R2, the rebase test with its control (same `uv run --script` setup).
- `guide/process.md`, `templates/inbox.md`, `docs/REFERENCE.md`, `skills/idea/SKILL.md`,
  `skills/status/SKILL.md`: R9. Then `sdlc.py record` so `.sdlc/setup.json` matches.
- `.sdlc/work/inbox.md` on this branch: intent tagged 2026-11-17-41 `[building]` here, the very
  edit this change retires; it goes back to the base branch's text, so the register on this
  branch is unchanged until ship deletes the seed.

## Work order

1. R1: the skills test, red; edit `SKILL.md` and `batch.md`; adjust the theme test.
2. R3: `next_up`'s `building` and the status lines, test first.
3. R4: `building` on `bugs` and `nits`, test first.
4. R5, R6, R7, R8: tests over behaviour that already holds (`groups`' claims, ship's tag-blind
   deletion, `_open_claims()` skipping `dropped`, `check` reading only tagged entries). Each test
   is shown failing by temporarily breaking the line it pins, then restored.
5. R2: the rebase test, with its control.
6. R9: the docs, `record`, `drift` clean; restore the register on this branch.
7. `./check.sh`.

## Tests

- R1: `test_intent_never_edits_the_register` (test_skills.py).
- R2: `test_an_inbox_commit_on_the_base_never_stops_an_open_change_s_rebase` (test_resolve.py,
  portable), control included.
- R3: `test_next_up_lists_what_open_changes_build`, `test_status_counts_and_lists_what_is_being_built`
  (test_next_up.py).
- R4: `test_bugs_names_the_change_that_fixes_each` (test_bugs.py),
  `test_nits_names_the_change_that_takes_each` (test_nits.py).
- R5: `test_an_untagged_seed_an_open_change_names_is_taken` (test_groups.py).
- R6: `test_ship_deletes_an_untagged_seed_its_idea_line_names` (test_bugs.py).
- R7: `test_a_dropped_change_gives_its_seed_back` (test_bugs.py: next_up, groups,
  inbox-commit).
- R8: existing legacy tests unchanged, plus `test_check_is_quiet_on_an_untagged_seed_a_change_names`
  (test_bugs.py).
- R9: `test_defaults.py` (shape, inbox note), `drift` empty after `record`.

## Rollback

`git revert` covers it all: no data is written, nothing published. A seed opened while this was
live carries no `[building]` tag; after a revert it still reads as taken, through `idea:`.
