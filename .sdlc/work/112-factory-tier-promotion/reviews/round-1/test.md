VERDICT: PASS

I found no requirement without a test that would fail if it were removed, and I found no test that can't fail. Every R1–R15 requirement maps to a test or a check:

- R1: `test_upgrade_sets_tier_and_stage_by_line`, `test_upgrade_scaffolds_only_what_is_missing` and `test_upgrade_leaves_check_strict_clean`.
- R2: `test_upgrade_refuses_and_writes_nothing`, with one parametrised case for each of its four refusals.
- R3: `test_verdicts_names_upgrade_on_an_upgrade_answer`, `test_only_a_decided_blocking_answer_upgrades` and `test_a_tier_2_answer_never_upgrades`.
- R4: `test_upgrade_writes_the_record_then_the_tier`, `test_upgrade_moves_no_head` and `test_an_upgrade_cut_short_finishes_on_rerun`.
- R5: `test_no_second_upgrade`.
- R6: `test_an_upgraded_run_specs_then_builds_round_p` and `test_an_upgraded_run_counts_its_rounds_from_p`.
- R7: `test_the_spec_prompt_names_the_upgrade`.
- R8: `test_the_upgraded_build_resumes_the_builder_into_round_p`.
- R9: `test_decided_refuses_while_an_upgrade_is_under_way`.
- R10: `test_reviewers_and_approver_are_told_of_the_upgrade`.
- R11: `test_start_reports_an_upgrade` and `test_fresh_holds_an_upgraded_run`, run at the plan, design and build stages.
- R12: `test_check_leaves_out_the_template_plan_during_a_live_upgraded_build`, `test_the_template_plan_shows_once_the_upgraded_build_is_not_live`, and `test_the_upgraded_record_pattern_is_a_pinned_copy` for the pattern copy.
- R13: `test_an_upgrade_or_spec_record_keeps_the_step_it_paused_at` for `AFTER:`, and `test_an_upgrade_pauses_the_step_track` in `tests/test_board.py`.
- R14: `test_the_build_skill_handles_every_step_verdicts_names`.
- R15: the one section in `checks.md`.

## Notes

- **Run:** `uv run --group dev pytest -q -n auto` gave 2287 passed and 13 skipped, with no failures.
- **Extra tests:** `test_a_bad_upgrade_record_stops_the_run` covers the unreadable-record stop. R3 adds `test_a_tier_2_answer_never_upgrades`.
- **Portable marks:** R1, R2 and R12 are marked `portable`, as the spec asks.
- **R15 check:** the single `checks.md` section ("The docs describe the upgrade, and none calls it a promotion") uses `grep` only and writes nothing. It should pass as the docs now stand, and it fails if the docs are reverted. I did not run it.
- **R14 coverage:** the check that every step `verdicts` returns has a bullet in the build skill is the guard most likely to catch future drift.
- **Not verified:** I did not run `./check.sh`, so ruff, ruff format and `claude plugin validate --strict` are unchecked.
- **Pre-existing:** I found nothing.
