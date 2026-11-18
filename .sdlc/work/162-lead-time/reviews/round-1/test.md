VERDICT: PASS

The tests cover every requirement, and each can fail without the change. The gate record (`build/round-1.gate.md`) shows `2989 passed, 28 skipped`, with ruff and `claude plugin validate` green. I ran no tests myself; the gate's count is the evidence.

## Notes

Requirement to test map:
- **R1:** `test_new_writes_when_the_change_was_opened_to_the_minute` covers both tiers and `test_new_writes_opened_under_github_numbering` covers GitHub numbering. `test_opened_goes_before_the_closing_line_without_created` covers the template with no `created:` line. The `id: 012` assertion is in the GitHub-numbering test.
- **R2:** `test_shipping_dropping_and_upgrading_keep_opened`.
- **R3:** no new test, as planned; the gate's `test_defaults.py` and drift check pass unchanged.
- **R4:** `test_lead_time_parts_sum_to_lead_and_overlapping_agents_count_once` and `test_without_a_landing_ready_waits_until_close`. `tests/test_modules.py` pins purity.
- **R5:** `test_lead_time_leaves_out_what_it_cant_know` is parametrized, and `test_lead_time_with_opened_after_closed_is_nothing` covers `opened` after `closed`. `test_agents_before_opened_are_clipped_to_it` covers the builder's D2 clip, which the plan records as a departure from the spec.
- **R6:** `test_the_lead_line_round_trips_with_minutes_and_a_source_word`.
- **R7, R8:** `test_close_times_a_factory_change_from_its_run_files`, plus `test_a_factory_change_with_no_landing_row_lands_at_its_tip` for the tip fallback.
- **R9:** `test_factory.py` and `test_land.py` assert the new `started`, `ended` and `since` keys. `test_close_reads_the_run_rows_the_factory_writes` pins closing's reader against rows the factory wrote. The `land-record-cases.json` fixture pins the board's copy.
- **R10:** the hand-built tests with and without transcripts, and `test_a_factory_change_from_before_the_times_reads_its_sessions`.
- **R11:** `test_a_change_without_a_usable_opened_says_so` (parametrized over `lead=none` and `lead=bad-opened`) and `test_timing_that_fails_drops_only_its_own_line`.
- **R12:** `test_a_dropped_change_records_no_lead`.
- **R13, R14, R15:** `test_lead_time_by_tier_and_way_with_unmeasured_counted_apart`, `test_without_a_lead_line_every_other_figure_is_as_it_was` and `test_the_report_shows_lead_time_under_cycle_time`.
- **R16:** docs only, as planned; ship shows the edit.

Checks: the change has no `checks.md`, so there is no acceptance check to review.

Open decisions D1–D3 in `decisions.md` are the builder's own defaults, each with a stated reason, and none blocks a test. I raise nothing against them.

- NIT: tests/test_archive.py: the `lead=bad-opened` path for `opened` after `closed` (decision D3) has no test of its own; only a malformed value is parametrized {tests S low}
