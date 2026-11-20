# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Twenty nits 191 had already settled

191-tests-paydown took in 26 nits and fixed or answered each one, but its `entries.md` retired
only five, so the other 21 stayed open in the register. Twenty of them are taken in here
(2026-11-19-78 was not). I checked each against the code as it stands, and each is still settled.
None needed an edit:

- **2026-11-19-7**: `_reached` and `_named` in `test_modules.py` have docstrings.
- **2026-11-19-8**: `test_land_mend_is_refused_on_either_of_its_files` (`test_prompts.py`).
- **2026-11-19-11**: `_bare_repo`'s docstring. Its author is conftest's autouse `git_identity`,
  which a clean CI box has too.
- **2026-11-19-17**: `test_the_report_shows_the_value_figures_in_its_window` checks the
  follow-through sentence against the JSON.
- **2026-11-19-20**: `test_retro_autonomy_rates_kept_defaults_without_the_landings_yes`.
- **2026-11-19-23**: the two kill tests share one bound, `STARTED_WITHIN`, with its reason.
- **2026-11-19-29**: answered in 191's notes. The check belongs to 173, a closed change whose
  folder is gone from `main`, so no run reads it again.
- **2026-11-19-38**: `test_an_ejection_is_recorded_and_amended_in` checks a stop row's `land`
  and `at`.
- **2026-11-19-40**: `test_an_indicator_that_cannot_start_is_a_failure_not_rows`.
- **2026-11-19-49**: `test_land.py`'s constants are hoisted as `ALREADY_MADE` and `MADE_REPORT`,
  and `test_train.py`'s is `ALREADY_MADE_REPLY`.
- **2026-11-19-51**: `test_a_line_one_shebang_is_not_a_comment`.
- **2026-11-19-55**: `test_a_stop_that_cant_be_recorded_still_stops`.
- **2026-11-19-56**: `test_a_change_with_no_start_leaves_its_commits_unknown` pins the row's
  `change`. The missing `n` is seed 2026-11-20-15, not taken in here.
- **2026-11-19-57**: `test_a_stop_before_any_change_moved_leaves_no_row` (`test_train.py`).
- **2026-11-19-67**: the Speed section is matched on the landing line's own labels.
- **2026-11-19-73**: `test_the_loop_rechecks_before_it_runs_accept`.
- **2026-11-19-76**: `test_an_uncached_script_skips_however_uv_words_it`.
- **2026-11-19-77**: `test_an_unreached_index_runs_the_script_again_from_the_cache`.
- **2026-11-20-2**: `test_no_doc_uses_a_retired_phrasing` lists one phrasing a line.
- **2026-11-20-4**: `east`'s docstring says why it is never `portable`.

## The nine raised since

- **2026-11-20-33**: the nit said `_last_experience` would raise on a non-numeric cell. It
  didn't: `indicators.report_rows()` already reads one as None. What it did get wrong was a
  number the question never offered: `7` read back as a rating of 7, and `2.5` as 2. Now only a
  whole 1 to 4 counts as a rating, and anything else is None. Pinned by
  `test_a_hand_edited_rating_reads_back_as_none`.
- **2026-11-20-32**: `_experience_text` now renders the rating and the last rating through
  `_num()`, the report's own "`—` for none" helper, so the dash is named in the code rather than
  left to `_table()`. The output is the same, so no test could fail on this change. The existing
  `_felt_row("—", ...)` assertions pin the output.
- **2026-11-20-10**: the test is now in `test_factory_decisions.py`, since `test_factory.py` was
  split. Its chained body is now two tests, the second parametrized. Each case fails alone under
  a mutation of `alternatives()`: dropping the source, the kind, or the options.
- **2026-11-20-22**: 197's `test_a_read_then_a_blank_heading_keeps_the_section_open` already
  covers the read side. Two tests now cover the rule's other side, one each way: a blank line
  then a heading ends a command still owing its exit, and a heading with no blank line before it
  is output.
- **2026-11-20-30**: `_neither_side()`'s True for a path git can't hash is never reached by a
  deleted moved file. `deleted_sides()` names only moved files still in the tree, so the deletion
  is refused as an edit outside the conflicted files. That is the right outcome, and
  `test_a_moved_file_the_resolution_deleted_is_not_carried` now pins it.
- **2026-11-20-16**, **-26**, **-29**, **-34**: fixed as `plan.md`'s table says.

## The guard against the commonest kind

The guard is `tests/test_suite_shape.py`'s `unused_fixtures()`, run by
`test_no_test_takes_a_fixture_it_never_uses`. It fails when any test asks for one of pytest's
own fixtures (`tmp_path`, `capsys`, `monkeypatch` and kin) and never names it, which is the kind
of nit -34 is. On the tree as it stood it found 30 more, and each one had its argument dropped.
The commonest `tests` nit overall is a weak or missing assertion, but only a reviewer can judge
that. Of the kinds a script can catch, this one is the commonest, and it is the decision raised
in the report.
