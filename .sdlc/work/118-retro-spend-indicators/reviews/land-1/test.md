VERDICT: PASS

No requirement from R1 to R9 lacks a test, and the full suite passes on the rebased tree. R10 is docs only. R11 is ship's step, so it isn't tested here.

## Notes

- **Rebase:** the builder's conflict resolution touched only `.sdlc/work/inbox.md`, which holds no code or tests. The register entries 80–88 are all present, and 2026-11-12-2 is gone as the builder said.
- **R1:** `test_words_are_counted_and_no_text_leaves` pins the per-stage and total counts. It also checks that a sentinel string appears in no event and no trailer body, so it fails if text leaks.
- **R2:** `test_every_tool_call_is_counted_with_its_error` covers:
  - names from `_prompt_name()`, such as `Bash:git:push`;
  - an error read from the matching result;
  - a call with no result counted with `error` unset;
  - the per-stage count, including a factory role's calls;
  - the total of 4 calls;
  - no path in any event.
- **R3:** `test_tool_lines_round_trip` and `test_a_close_from_before_tool_lines_is_unrecorded` cover the `Sdlc-Tool` lines and the unrecorded case.
- **R4:** `test_comment_lines_by_suffix` covers the `#`, `//`, `--` and `<!--` markers, `unknown_lines` and prose files.
- **R6:** `test_spend_names_a_change_twice_its_tier_median` and `test_a_tier_with_two_changes_names_no_outlier` cover the median and outlier rules.
- **R7:** `test_spend_ranks_the_tools` covers the most-called and most-errors lists.
- **R5 and R8:** `test_spend_lists_each_change_and_says_what_is_unrecorded` runs through a git fixture with one recorded change and two unrecorded, each with its own `why`. It also checks that per-change rows print only with `--metrics`, as decisions D1 and D2 settled.
- **R9:** `test_the_report_renders_spend` checks the `## Spend` section renders with no placeholder left, and checks the `TEMPLATE_READS` miss for an old override. The `TEMPLATE_READS` entry for `retro.md` is in `sdlc.py`.
- **Minor:** the new `skills/retro/SKILL.md` bullet ends with "a few changes are anecdote;" and a semicolon, where the clause seems unfinished. It's a wording point and doesn't affect any test.
- **`checks.md`:** none exists for this change, so there is nothing to judge or run.
- **Run:** `uv run --group dev pytest -q -n auto` gave 2237 passed, 13 skipped, no failures.
