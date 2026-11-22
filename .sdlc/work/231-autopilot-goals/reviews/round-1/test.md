VERDICT: PASS

The tests cover every requirement, and I found no test that can't fail.

## Notes

Gate record `build/round-1.gate.md` is `GATE: PASS` with `./check.sh` exit 0, "4044 passed, 29 skipped", and plugin validation passed. I read the tests and ran none myself.

Requirement-to-test map:
- **R1:** `test_goals_come_from_the_real_status_json` goes through the real `sdlc.py`. It covers a struck item left out, a title resolved to its id, a seed no longer in the register left out, and the empty case with no doc.
- **R2:** `test_a_goal_is_read_by_its_form` covers all three forms, a struck or unknown id (`M2`, `G2`, `M999`), the lowercase and "and more" cases read as stated, and empty input.
- **R3:** `test_a_goal_only_narrows_the_candidates` checks that every goal form gives a subset in the same order. It also shows that `--themes` still applies, and that `autopilot_config`, `hold_causes` and `_default_guards` take no `goal` parameter.
- **R4:** `test_the_preview_proposes_a_goal_when_none_is_stated` covers the milestone order, a milestone with no candidate skipped, the theme fallback, the tie-break, the cap of three alternatives and the no-goal case.
- **R5:** `test_autopilot_preview_writes_nothing` (extended) and `test_the_preview_names_a_goal_from_the_direction_doc` cover the question, `shown`, both warnings, the `M999` refusal and the no-goal case.
- **R6:** `test_autopilot_begin_refusals` has the `no goal` and `a closed milestone` cases. `test_autopilot_begin_writes_the_state_once` checks the goal, the scope and the register start, and that a fenced entry isn't counted.
- **R7 and R12:** `test_the_wave_brief_names_the_goal` and `test_a_run_begun_without_a_goal_resumes`.
- **R8:** `test_the_planner_places_every_candidate` covers 13 refusal cases with their messages. `test_planner_reply_is_checked_by_the_script` covers the mend path.
- **R9:** `test_a_seed_the_planner_leaves_is_left_for_the_person` and the end-to-end test both compare the register and the direction doc byte for byte after the run.
- **R10:** `test_the_intent_brief_carries_the_plan` checks the `Planned:` line. It sets the planner's tier to 1 and the draft's to 2, so it fails if the planner's tier overrides the draft's.
- **R11:** `test_the_summary_says_whether_the_register_grew` covers the grew, even and drained cases, the counts, the sections, and a stored end count.
- **R13:** `test_the_skill_quotes_the_preview_question`.

- NIT: tests/test_autopilot.py:1735: the "empty reason" case rewrites the WAITS line to a bare reason; no case gives a WAVE or LEAVE line an empty reason, which R8 also names {tests S low}
- NIT: tests/test_autopilot.py:1696: no case puts a `LEAVE` heading-less before any group to show LEAVE is allowed anywhere. Only the group-less WAVE case exists. {tests S low}

Checks: the change has no `checks.md`, so there are none to review.

Command run: none.
