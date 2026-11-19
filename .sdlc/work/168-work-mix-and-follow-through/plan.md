---
id: 168
slug: work-mix-and-follow-through
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 168 — The retrospective reports work mix, follow-through and time to users · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/metrics.py`: R11 `bg` regex in `_shell()`; R12 `_program()`'s `uvx`/`npx` slice; R13
  `HAND_GATE_RE` takes an optional quote; the docstring says what `bg=` counts and since when.
- `scripts/sdlc.py`: `_change_record()` reads `fixes:` with `frontmatter_list()` (R4), beside
  `reworks`. Nothing else.
- `scripts/retro.py`:
  - `_register_at(home, base, cache)`, factored out of `_none_themes()`, which then uses it.
  - `WORK_CLASSES`, `DEBT_THEMES`, `_work_class()` and `_work_mix()` (R1–R3).
  - `_time_to_users()` (R5, R6): one `for-each-ref` for tag times, `rec["release"]` or
    `_release_of()` per change, `sdlc._release_tags()` for `releases`.
  - `_follow_through()` (R7–R9): registers at the retrospective and its first parent through
    `git show`, retired ids from one `git log --first-parent --format=%s`, milestones through
    `direction_items()` and `_milestone_verdicts()`, open names from `sdlc.change_dirs()`.
  - `value_band()`, the one function both `retro()` and `retro_report()` call; `retro()` keeps
    each change's numstat paths and spreads the band into its output; `retro_report()` keeps its
    rows' paths and passes the band to `render_report(..., value=)`.
  - `render_report()` appends three sentences to `values["window"]` (R10), nothing when `value` is
    None.
- Reused, never re-derived: `sdlc.parse_entries`, `ref_matches`, `ideas_of`, `is_bug`, `is_nit`,
  `entry_theme`, `work_rel`, `INBOX`, `CHANGE_FOLDERS`, `MANIFEST`, `HOST_DIR`,
  `direction_items`, `_direction_text`, `_milestone_verdicts`, `_release_tags`, `inbox_entries`,
  `indicators._unquote`, `_release_of`.
- `tests/test_metrics.py`: the R11–R13 cases.
- `tests/test_retro.py`: `test_a_closed_change_carries_its_fixes_line` (R4), beside the other
  closed-record tests, since its fixture builds closes; the R1–R3 and R5–R10 tests the spec names;
  `_close()` gains a `fixes` argument; `test_retro_and_its_report_show_the_same_figures` extended.
  Two more than the spec names: `test_work_mix_shares_are_null_with_nothing_classed` (R2's null
  shares) and `test_without_a_value_band_the_window_is_as_before` (R10's old caller).
- `docs/RETRO-SCORECARD.md`: only the three Status lines; the wave lists are left to whoever
  closes the wave.
- `docs/REFERENCE.md` *Retrospectives*, `skills/retro/SKILL.md` Step 0, `docs/RETRO-SCORECARD.md`
  (S2, S12, S13 captured): R14.

## Work order

1. **Nits (R11–R13)**: the test cases first, seen failing, then the three regex/slice edits and the
   docstring. Stands alone.
2. **`fixes` on the record (R4)**: the test, then one line in `_change_record()`.
3. **Work mix (R1–R3)**: `_register_at()` (with `_none_themes()`'s tests still green), then the
   class rules and the count, written into `retro()` through `value_band()` with only
   `work_mix` in it.
4. **Time to users (R5, R6)**: added to `value_band()`.
5. **Follow-through (R7–R9)**: added to `value_band()`.
6. **The report (R10)**: `retro_report()` calls `value_band()`; `render_report()` gains `value=`.
7. **Docs (R14).**

Each step ends with its own tests run by name and the tree working.

## Tests

- R1: `test_work_mix_classes_each_change_by_its_first_signal`.
- R2: `test_work_mix_counts_an_unreadable_impact_as_unmeasured_never_a_class`,
  `test_work_mix_shares_are_null_with_nothing_classed`.
- R3: `test_a_change_touching_only_the_process_is_process_work`.
- R4: `test_a_closed_change_carries_its_fixes_line`.
- R5: `test_time_to_users_is_the_median_from_close_to_the_first_release`.
- R6: `test_an_unreleased_change_is_counted_apart_from_time_to_users`.
- R7: `test_follow_through_scores_the_last_retrospective_s_seeds`.
- R8: `test_follow_through_scores_the_milestones_open_at_the_last_retrospective`.
- R9: `test_without_an_earlier_retrospective_follow_through_is_unmeasured_not_zero`.
- R10: `test_the_report_shows_the_value_figures_in_its_window`,
  `test_retro_and_its_report_show_the_same_figures` (extended),
  `test_without_a_value_band_the_window_is_as_before`.
- R11: `test_a_command_ending_in_a_lone_ampersand_goes_to_the_background` (new cases).
- R12, R13: `test_a_test_run_is_known_by_its_program` (new cases),
  `test_a_hand_gate_is_counted_as_a_check` (quoted form).
- R14: review only.

## Rollback

`git revert` undoes all of it: retro writes nothing new, no trailer key is added, no template or
config key changes. One thing it doesn't undo: `Close` commits made while this was in place may
carry a higher `bg=` count for the same behaviour (R11's wider shapes). They stay in history as
written; nothing reads `bg=` as more than a lower bound, so nothing needs undoing.
