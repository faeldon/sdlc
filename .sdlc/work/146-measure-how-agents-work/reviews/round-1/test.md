VERDICT: PASS

Every requirement R1–R15 has a test that fails without it. R16 is docs-only and the spec says to review it, not test it. I did not run `claude plugin validate`, so I can't speak to that part of `./check.sh`.

## Notes
- **R1/R2:** `test_a_role_s_behaviours_are_counted_from_its_transcript` uses one of each behaviour, including an interrupted call, and asserts every count equals 1.
- **R3:** `test_a_shell_edit_is_known_by_its_command` has 20 parametrised cases. They include the negative shapes: `/tmp` redirects, `grep '>'`, a heredoc fed to `cat`, and `sed -n`.
- **R4:** `test_a_backgrounded_command_is_known_by_its_result` and the `&` test cover `run_in_background`, the harness moving a long command to the background, and a trailing `&`, with `&&` and `2>&1` as negatives.
- **R5/R6:** the runner cases include the host's check, the hand gate, and words like `grep pytest` that only name a runner. The broke cases cover an edit before the run, no edit before the run, a failing assertion, and a result given as a list of text blocks.
- **R7–R12:** the tests cover each requirement, including that no marker text reaches a trailer line and that an old `Close` body parses unchanged.
- **R9:** `test_measuring_reads_each_transcript_once` runs end to end through `measure_change` and checks the model read from `costs.jsonl`. It also tolerates a bad `costs.jsonl` line.
- **R13–R15:** the retro tests cover grouping by role and model, medians, the report table rows, unrecorded versus zero, and `--metrics` lean versus full.
- **Independence:** the tests share no mutable state.
- **Mocks:** they stub only `_behaviour`, to prove R10's failure path, and `_lines`, to count reads.
- **`checks.md`:** the change has none, and none is needed. Everything is covered by suite tests.
- **Test command:** `uv run --group dev pytest -q -n auto` gave 2623 passed, 18 skipped.
