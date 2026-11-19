---
id: 178
slug: comment-health
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 178 — Comment health as an indicator · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `.sdlc/comment-health.py` (new): a PEP 723 script with no dependencies, shaped like
  `.sdlc/function-heat.py`: a module docstring that is its contract, pure functions over source
  text (`scan()`, `docstrings()`, `words()`, `is_narration()`, `long_functions()`, `measure()`,
  `rows()`), `hot()` and `main()`, the only parts that run git.
- Reused, not copied: `function-heat.py`, loaded by path (`_load_heat()`), for `_git`,
  `base_branch`, `heat`, `rank` and `FILES`. `retro.py`'s bytes-over-4 estimate (`n // 4`, from
  `prose_metrics()`) is matched, not imported: the script is this repo's own and loads nothing from
  `scripts/`.
- `tests/test_comment_health.py` (new), marked `portable`, loading the script by path as
  `tests/test_function_heat.py` does, and `retro.py`/`indicators.py` for R1 and R4.
- `tests/test_windows.py`: `.sdlc/comment-health.py` added to `SCRIPTS` (R14).
- `.sdlc/config.toml`: `retro.indicators` gains the command after function heat, with a comment
  (R13).
- `docs/RETRO-SCORECARD.md`: S17's row and the Wave 3 line say done as 178; a *Supporting: comment
  health* entry in the Quality pillar, Cost as its guardrail (R15).

## Work order

1. **Per-file measures from text** (R2, R7, R8, R11): `scan()` (tokenize once; comment tokens with
   line, text, full-line or trailing; directives, a line-1 shebang and the PEP 723 block left
   out), `docstrings()` (module, class and function docstring spans and literal bytes),
   `words()`/`is_narration()`, and `measure()` putting them together, returning None on a file
   that doesn't parse or tokenize. Tested on fixtures with known answers.
2. **Long functions** (R5): `long_functions(tree)`, top-level functions and methods of top-level
   classes spanning `LONG` lines or more, with whether each has a docstring.
3. **Rows** (R1, R3, R4, R5 no-share, R12): `rows()` builds the JSON Lines in a fixed order: per
   file (density, then narration share) in path order, the `all scripts` rows, long functions,
   hot functions. A share of nothing is not printed. Tested through `indicators.host_rows()` and a
   round trip through `retro._indicators_text()` and `indicators.report_rows()`.
4. **Hot functions** (R6): `hot()` calls function heat's `heat()` and `rank()` and keeps rows with
   a commit, then reads each one's docstring from the base branch's source. Tested in a scratch
   repo with a `Retrospective` commit, plus an AST check that the script defines no
   `blamed`/`heat`/`rank`.
5. **main()** (R9, R10): files from `git ls-tree` on the base branch, read with `git show`; a bad
   file skipped; no base branch exits 1 with one stderr line. Tested by running the script in a
   scratch repo.
6. **Wiring** (R13, R14, R15): config entry and its test, `SCRIPTS`, the scorecard.

## Tests

All in `tests/test_comment_health.py` unless named otherwise.

- R1: `test_its_output_reads_as_indicator_rows`
- R2: `test_density_counts_comment_and_docstring_lines_once`
- R3: `test_the_band_counts_files_below_and_above`
- R4: `test_rows_read_back_from_a_report`
- R5: `test_long_function_coverage_counts_methods_and_skips_short_ones`,
  `test_no_long_functions_prints_no_share`
- R6: `test_hot_functions_are_function_heats_with_a_commit`, `test_hot_reads_function_heat_not_a_copy`
- R7: `test_narration_is_told_from_explanation` (a trailing comment and a block with no words
  too), `test_words_split_identifiers_and_drop_short_and_stopwords`
- R8: `test_token_share_is_comment_and_docstring_bytes_over_all_bytes`
- R9: `test_it_reads_the_base_branch_and_writes_nothing`
- R10: `test_a_file_that_does_not_parse_is_skipped_not_raised`, `test_no_base_branch_exits_one`
- R11: `test_rows_carry_no_source_text`
- R12: `test_this_repos_rows_stay_under_the_evidence_limit`
- R13: `test_this_repo_runs_comment_health`
- R14: `tests/test_windows.py`'s existing parametrized checks, over the new `SCRIPTS` entry.
- R15: no test; an acceptance check in `checks.md` greps the S17 row, the Wave 3 line and the
  *Supporting: comment health* entry.

## Departures while building

- A line-1 shebang (`#!`) is a directive, not a comment: `scripts/sdlc.py` opens with one, and
  it is for the shell, as `# noqa` is for ruff. The spec's directive list doesn't name it.
- A function nested in a long top-level function counts only as its holder, which is itself long
  when the nested one is (R5's test says so).
- `hot()` returns each hot function's having a docstring, and `rows(measured, hot)` takes that
  list, so the rows are tested without git.

## Rollback

`git revert` undoes all of it: the script writes nothing, publishes nothing, and no host's config
names it. A retrospective report already committed with its rows keeps them; the next one simply
shows no last value for them, which needs no undo.
