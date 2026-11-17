VERDICT: CHANGES

- CHANGE: tests/test_factory.py: `is_read("cat a > 2")`, `"cat a >2"` and `"echo hi >> 1"` all return True, but they write a file named `2` or `1`. The redirect check accepts any all-digit target, and that is only safe after `>&` (`2>&1`). Add these as NON_READS rows, then fix `is_read()` in `factory.py` so a bare digit target passes only after `>&` or `&>`. Spec Design step 4 allows "a descriptor (`2>&1`)", not a file named by a digit. Keep `cat a 2>&1` as a READS row.

## Notes

- **Run:** `uv run --group dev pytest -q -n auto` gave 2255 passed, 13 skipped, no failures. I did not run `./check.sh`.
- **R1–R4 and R6–R8 are covered and each test can fail:**
  - R1: `test_a_read_is_only_what_the_script_can_tell_changes_nothing` holds every spec row. `NON_READS` can fail, and I checked by hand that `sort -o`, `git log --output`, `&`, heredoc and `head > b` are refused.
  - R2: `test_a_read_showing_its_output_needs_no_exit`.
  - R3: `test_a_silent_read_still_needs_its_exit` covers both a bare `$` and a fence-only or blank-only reply.
  - R4: the new `uv run pytest -q | grep passed` parametrized case.
  - R6: `test_a_builders_read_needs_no_exit`.
  - R7: `test_no_exit_is_not_a_read` pins `NO_EXIT`, and `test_a_build_mend_is_refused_when_verdicts_names_none` uses the non-read command.
  - R8: the new assert in `test_skills.py` checks both prompts for the phrase.
- **R5:** `test_119s_landing_replies_pass` runs both replies through `land-verdicts`. It is gated on `needs_uv`, and `uv` was present, so it ran.
- **Lower priority:** `read_evidence()` counts any non-blank, non-fence line after a read as its output. That includes prose before the next `##`, so a silent `cmp` followed by a trailing sentence passes. The spec says "non-blank output line", so this is within spec, but you could mention it.
- **Missing coverage:** no table row covers `find` or `sort` with their refused options. I checked `sort -o` by hand. Optional: add `find . -exec rm {} ;` and `sort -o f g` to NON_READS.
- **`checks.md`:** none exists for this change. Spec Verification has a by-hand step (feeding `read_evidence()` the R5 fixtures, then swapping in `uv run pytest -q`). `test_no_exit_is_not_a_read` and the R5 test cover that.
