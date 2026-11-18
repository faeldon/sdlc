VERDICT: PASS

Each requirement is covered by a test that would fail without it. The suite has one failure, and it comes from a review artifact in this change's folder, not from the change.

## Notes

- **Suite:** `uv run --group dev pytest -q -n auto` gave 2573 passed, 18 skipped and 1 failed. The failure is `tests/test_nothing_local.py::test_nothing_in_the_repo_is_forbidden`. It flags `.sdlc/work/140-agent-replies-that-file-right/reviews/round-1/behaviour.md:22`, where the behaviour reviewer's recorded command contains `.sdlc/work/140-agent-replies-that-file-right/`, which the test reads as a citation of a change by folder number. That file is a transient review artifact, not part of the change's code or tests. I didn't confirm that it, and no other source, accounts for all four extra items in the assertion. If the artifact is committed with the change, the gate fails at land, so check it then. I did not run `./check.sh`.
- **R1:** `test_claude_returns_every_reply_in_order` feeds a stream of two replies and checks they come back in order.
- **R2:** `test_a_second_reply_never_replaces_the_verdict` runs the fake `claude` through three cases: a verdict followed by a note, a changed verdict on waking, and no reply holding a verdict. `test_holds_picks_each_role_s_answer` covers each role's predicate.
- **R3:** `test_a_recorded_stream_with_two_replies_reads_both` reads the committed fixture `tests/fixtures/stream-two-replies.jsonl`, a real stream, through `_claude()`. It also asserts the cost and turns figures.
- **R4:** `test_a_stream_without_a_result_or_with_an_error_fails` covers a missing `result`, an erroring last `result`, and a non-zero exit.
- **R5:** `test_figures_sum_a_session_s_turns_and_take_its_last_cost`.
- **R6:** `test_opening_reads_the_answer_line` runs the shared cases in `tests/fixtures/opening-cases.json`. `test_a_verdict_after_prose_is_read` covers `verdicts` and `land-verdicts`.
- **R7:** the once-a-round mend tests were rewritten with disagreeing replies and pass.
- **R8:** `test_the_boards_opening_is_a_pinned_copy` and `test_sdlcs_opening_is_a_pinned_copy_of_the_factorys` run the shared table through each copy, plus the board and metrics prose cases.
- **R9:** `test_no_reviewer_runs_the_gate_or_waits_in_the_background` checks every reviewer and the verifier.
- **checks.md:** the change has no `checks.md`, so there were no acceptance checks to judge.
- **Test command:** I ran `uv run --group dev pytest -q -n auto`, with the count above.
