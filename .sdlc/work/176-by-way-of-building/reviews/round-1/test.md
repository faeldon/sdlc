VERDICT: PASS

## Notes

- Every requirement has a test that would fail without it. R13 is covered by review and grep, as the plan says.
  - R1 (`test_a_change_with_no_sdlc_mode_counts_as_unknown_way`) closes a change with a `decision.md` and no `Sdlc-Mode`. It asserts that change counts as `unknown`, not `factory`.
  - R2 (`test_lead_time_is_given_by_way_across_tiers`) checks the per-way median and p85, the empty `unknown` way, and that the per-tier groups are unchanged.
  - R3 (`test_throughput_counts_each_week_by_way_and_by_work_class`) uses exact row equality, with 0s present, and asserts both sums equal `total`.
  - R4 (`test_the_report_s_throughput_shows_work_classes`) asserts the rendered row reads `fix: 1`, so it would fail if the report left the change unclassed.
  - R5 (`test_by_way_gives_every_figure_for_each_way_with_its_n`) checks that every part names every way, that `changes` sums to the window's closed count, and that `lead` and `escapes` are copies of the R2 and R7 figures.
  - R6 (`test_hand_built_cost_compares_in_tokens_and_is_missing_in_dollars`) checks that the `manual` `usd.median` is null with `built by hand: 2`, that `tokens.n` is 2, and the `missing_because` reasons on the other ways.
  - R7 (`test_escape_rate_is_split_by_the_introducing_change_s_way`) covers an introducer that history doesn't hold, which reads `unknown`. It also covers a way with 0 changes, whose rate is null, and that the way escapes sum to the window's total.
  - R8 (`test_the_report_compares_the_ways_of_building`) asserts exact table rows, `–` for nulls, the order after the follow-through text, the new throughput columns, and that `render_report` with no `by_way` omits the table.
  - R9 and R10 (`test_a_grouped_seed_retired_by_inbox_commit_reads_dropped`) cover one seed grouped by id and one by title, a seed deleted with no `Retire` subject (still `vanished`), the `retired_entries()` output, and that `retro._retired_ids` is gone.
  - R11 has two tests: `test_a_milestone_whose_grouped_seeds_were_retired_follows_through_as_dropped` and `test_status_counts_a_milestone_with_a_retired_seed_done`. The first covers both `dropped` and `done` milestones.
  - R12 (`test_a_change_touching_only_setup_s_record_is_process_work`) closes a change touching only `.sdlc/setup.json` and asserts it is classed `process`.
- I did not open the body of `test_status_counts_a_milestone_with_a_retired_seed_done` in `tests/test_next_up.py`. I confirmed only that it exists and that the gate passed.
- The gate record `build/round-1.gate.md` reads `GATE: PASS` for `./check.sh`: `3307 passed, 29 skipped`. I ran nothing myself.
- There is no `checks.md` for this change, so there are no acceptance checks to review.
- No nits.
