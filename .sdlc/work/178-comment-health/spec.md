---
id: 178
slug: comment-health
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 178 — Comment health as an indicator · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code. 177 has landed: `indicators.host_rows()` reads a command's rows, and `_indicator_rows()` sets `last` and `change` against the last retrospective's report, read back by `(name, unit)`. `_evidence()` runs each `retro.indicators` command on its own, with `EVIDENCE_TIMEOUT` (60 s) and `EVIDENCE_LIMIT` (20,000 characters) each. If output gets cut, it is never read as rows. The report has no pillars yet. Indicator rows show in `## Indicators` (`_indicators_text()`), and grouping them by pillar is S14's job (see the open questions). The scripts measured are the twelve `*.py` files under `scripts/` and `plugins/factory/scripts/` on the base branch.

All tests below are in a new `tests/test_comment_health.py`, marked `portable`, which loads the script by path the way `tests/test_function_heat.py` does.

1. **R1. Rows in 177's shape.** `.sdlc/comment-health.py` prints JSON Lines on stdout. `indicators.host_rows()` reads the output as `(rows, None)`: every `name` and `unit` is a fixed string or a repo path, under `NAME_MAX`/`UNIT_MAX`, and no `(name, unit)` appears twice. `test_its_output_reads_as_indicator_rows` runs `host_rows()` on the script's output for a scratch repo and fails on any reason it gives.
2. **R2. Per-file density.** For each measured file there is a row `{name: <path>, unit: "comment density"}`. Its value is the file's comment lines plus docstring lines, divided by its non-blank lines, rounded to 3 places. Lines that are both count once. The PEP 723 block and tool directives (`# noqa`, `# fmt:`, `# type:`, `# pragma`) are not comments. `test_density_counts_comment_and_docstring_lines_once` checks a fixture with a known answer.
3. **R3. The band.** A row `{name: "all scripts", unit: "files outside 0.10-0.40"}` counts the files whose density falls outside `BAND = (0.10, 0.40)`. A second row, `{name: "all scripts", unit: "comment density"}`, gives the density across all files. `test_the_band_counts_files_below_and_above` fails if a file at 0.05 or 0.45 is missed, or if one at 0.10 or 0.40 is counted.
4. **R4. The trend comes from the report, not a second clock.** The trend across the window is the report's existing `Last retrospective` and `Change` columns. These work only while names and units stay the same between runs. `test_rows_read_back_from_a_report` renders the rows through `retro._indicators_text()`, reads them back with `indicators.report_rows()`, and fails if any row's `(name, unit)` doesn't come back with its value.
5. **R5. Docstring coverage of long functions.** A long function is a top-level function, or a method of a top-level class (named `Class.method`), that spans at least `LONG = 30` lines. The script prints `{name: "long functions (30+ lines)", unit: "functions"}` and `{…, unit: "share with a docstring"}`. A docstring is a non-empty `ast.get_docstring()`. With no long functions, only the count row prints, because a share of none isn't a number. Two tests cover this: `test_long_function_coverage_counts_methods_and_skips_short_ones` and `test_no_long_functions_prints_no_share`.
6. **R6. Docstring coverage of hot functions.** A hot function is one that `function-heat.py`'s `rank()` keeps for its file and that has at least one commit since the last retrospective. The script prints the same two rows under the name `"hot functions"`, with the same no-share rule. It gets the hot set by loading `function-heat.py` by path and calling its `heat()` and `rank()`, never a copy of them. Two tests cover this: `test_hot_functions_are_function_heats_with_a_commit` (a scratch repo with a `Retrospective` commit, where a function touched after it is hot and an untouched one is not) and `test_hot_reads_function_heat_not_a_copy` (an AST check that the script defines no `blamed`/`heat`/`rank` of its own).
7. **R7. Narration share.** Comments are read with `tokenize`, never by text matching, so a `#` inside a string is not a comment. A comment block (consecutive full-line comments, or one trailing comment) of at most `NARRATION_MOST_LINES = 2` lines is narration when at least `NARRATION_OVERLAP = 0.5` of its words also appear in the code line it describes. That line is the next non-blank code line for a block, or the comment's own line for a trailing one. Words are lowercase alphabetic runs of 3 or more letters, identifiers are split on `_` and camelCase, and a short `STOPWORDS` set is removed. A block with no words is never narration. The script prints `{name: <path>, unit: "narration share"}` per file that has comments, and `{name: "all scripts", unit: "narration share"}`. The value is the narration comment lines divided by all comment lines, with docstrings and directives counted in neither. `test_narration_is_told_from_explanation` pins both directions: `# increment the retry count` above `retry_count += 1` is narration, and `# A rerun resumes here, so the push never repeats` above `_push(home)` is not. A 3-line block that restates its line is still not narration.
8. **R8. Comments' share of what agents read, estimated from the files.** The script prints `{name: "all scripts", unit: "comment token share"}`, which is the UTF-8 bytes of every comment token (trailing ones included, directives and the PEP 723 block left out) plus every docstring literal, divided by all the files' bytes. It also prints `{…, unit: "comment est. tokens"}`, which is those bytes divided by 4, the estimate `prose_metrics()` already uses. `test_token_share_is_comment_and_docstring_bytes_over_all_bytes` checks a fixture with a known answer.
9. **R9. It reads the base branch and writes nothing.** Files are listed with `git ls-tree` and read with `git show <base>:<path>` from the base branch that `function-heat.py`'s `base_branch()` resolves. Uncommitted edits and the checkout's branch change nothing. `test_it_reads_the_base_branch_and_writes_nothing` fails if a side-branch edit shows up in the output, or if `git status --porcelain` changes.
10. **R10. A bad file costs its own rows, not the run.** A file missing on the base, or one that fails `ast.parse` or `tokenize`, gives no rows and is left out of the totals. The script still exits 0 and prints every other row. Without a base branch it exits 1 with one line on stderr, as `function-heat.py` does. Two tests cover this: `test_a_file_that_does_not_parse_is_skipped_not_raised` and `test_no_base_branch_exits_one`.
11. **R11. Only names and numbers.** No row carries comment text, a docstring, or any source text. `test_rows_carry_no_source_text` puts a unique marker string in a fixture's comments and fails if it appears in the output.
12. **R12. Under the evidence limit.** At the widest numbers and with this repo's real file list, the output stays under `retro.EVIDENCE_LIMIT`. `test_this_repos_rows_stay_under_the_evidence_limit` follows `test_function_heat.py`'s test of the same name.
13. **R13. Set in this repo's config.** `.sdlc/config.toml`'s `retro.indicators` lists `uv run --quiet --script .sdlc/comment-health.py` after function heat, with a comment saying what it measures. `test_this_repo_runs_comment_health` fails if the entry is missing.
14. **R14. It runs on Windows.** `.sdlc/comment-health.py` is added to `tests/test_windows.py`'s `SCRIPTS`. That brings it under the existing checks: no top-level platform import, `encoding="utf-8"` on every text `subprocess.run`, and no `shell=True`.
15. **R15. The scorecard records it.** In `docs/RETRO-SCORECARD.md`, the S17 row and Wave 3 line say it is done as 178. The Quality pillar gets a *Supporting: comment health* entry with what, why, where and status, with Cost (`comment est. tokens`) as its guardrail. No test covers this; the review checks it.

## Design

**One new script, beside function heat.** `.sdlc/comment-health.py` is a PEP 723 script with no dependencies. It has the same shape as `function-heat.py`: a module docstring that is its contract, pure functions that take source text, and one `main()` that runs git.

- **Reuse.** `_load_heat()` loads `Path(__file__).with_name("function-heat.py")` with `importlib`. From it the script uses `_git`, `base_branch`, `functions`, `heat`, `rank`, `TOP` and `FILES`. The base branch, the last-retrospective boundary and the hot ranking therefore can't drift between the two indicators. This uses `importlib` as the repo's tests do, and core's "loaded by path" rule doesn't apply: both files are this repo's own, under `.sdlc/`.
- **Files.** `git ls-tree -r --name-only <base> -- scripts plugins/factory/scripts`, filtered to `*.py`. That gives twelve files today, and a new script is picked up with no list to keep by hand.
- **Per file, from its text:**
  - `scan(source)` runs `tokenize` once. It returns the comment tokens, each with its line, text and whether it is full-line, leaving out directives and the PEP 723 block.
  - `docstrings(tree)` returns the line spans and literal byte lengths of the module, class and function docstrings.
  - From these come the density (R2), the comment blocks and their target code lines (R7), and the comment bytes (R8).
  - `long_functions(tree)` covers top-level functions and methods of top-level classes (R5). The trackers are classes, so their methods would otherwise be invisible.
- **Narration** is `is_narration(block_words, code_words)`, a pure function with its thresholds as module constants. It is meant to be narrow. The signal is read as a trend window over window, so a rule that never changes matters more than one that catches everything. A long block is always counted as explanation.
- **Hot functions.** `heat(root, base, FILES)`, then `rank()` per file, keeping rows with `commits >= 1`. This runs `git blame` on the four files a second time, after `function-heat.py` does. Each command has its own 60 s budget in `_evidence()`, so the cost is time, not a risk of being cut off (see Verification).
- **Rows.** `rows(...)` builds the JSON Lines in a fixed order: the per-file rows in path order, then the `all scripts` rows, then long functions, then hot functions. It uses `ensure_ascii=False`, as `function-heat.py` does. Values are rounded to 3 places, and counts are ints.
- **Where it shows.** It shows under `## Indicators`, as the second command's table. `last` and `change` come from 177's read-back, which is the "trend across the window". Placing the rows in a Quality section is S14's work, since the report has no pillars yet.

Edge cases: a file with no non-blank lines gives no density row. A file with no comments gives no narration row. An empty set gives no share (R5, R6). A file that doesn't parse is skipped (R10). If there is no `Retrospective` commit, function heat's own rule applies: the whole history counts.

## Contracts touched

- **The scripts run on Windows** (AGENTS.md; `tests/test_windows.py`). The script uses `encoding="utf-8", errors="replace"` through `function-heat.py`'s `_git`, no `shell=True`, no platform imports, and no text writes at all. It is added to `SCRIPTS` (R14), so the AST checks cover it.
- **Nothing about a project or a workspace** (`tests/test_nothing_local.py`). Fixtures use neutral code (`retry_count`, `reopen-drafts`), and no home path appears anywhere.
- **Mechanism vs. policy / "the core never parses a language"** (RETRO-SCORECARD.md, *structural debt index*). The script is this repo's own and is named only in this repo's config. Nothing in `scripts/`, `defaults/` or `templates/` changes, so no host gets it, and `indicators.py`'s line-marker `comment_lines()` stays language-neutral. Neither `drift` nor `record` is involved.
- **The indicator row shape** (177, `indicators.host_rows()`). The script stays inside it and adds no new keys. A row's `extra` keys aren't rendered today, so nothing depends on them.
- **Retrospectives write only their report** (`retro()` is read-only apart from it). The script writes nothing (R9), so `retro-commit`'s clean-tree rule still holds.
- **REVIEW.md, "a path compared as text between two sources".** Paths come from `git ls-tree` and go straight back to `git show` as git wrote them, never through `Path`/`str()`. **REVIEW.md, "a transcript's shape assumed".** Avoided entirely: no transcript is read (see below).

No invariant needs to change.

## Alternatives rejected

- **A model call, or an NLP library, to judge narration.** The script must run offline, quickly and identically every time, with no dependencies (`dependencies = []`). A paid call inside a retrospective's evidence is also a cost that S17 is meant to measure, not add to.
- **Measuring "agent input tokens" from transcripts.** Hand-built sessions live in each machine's `~/.claude/projects/`, outside the repo. `metrics.py` records edits, not reads, and `costs.jsonl` has token totals but no per-file reads. The figure would vary by machine, and REVIEW.md warns against assuming a transcript's shape. The file estimate is what the seed's own "about 30%" was based on.
- **Copying function heat's blame code** to find hot functions. Two copies of the boundary and ranking would drift, which is why R6's test forbids it.
- **A band flag as an `extra` key on each row.** The report doesn't render `extra`, so the flag would be invisible. A count row (R3) shows in the table and trends.
- **Using `indicators.comment_lines()`.** It counts only `#`-marked lines added in a diff, treats docstrings as code, and would read a `#` inside a string as a comment. That is right for a language-neutral core, but wrong for a Python-only measure of whole files.
- **Folding the signals into `function-heat.py`.** That would make one command's output larger, closer to the 20,000-character cut, and mix two questions into one table.
- **Counting nested functions as long functions.** They belong to the function that holds them, as in `function-heat.py`'s `functions()`.

## Verification

```bash
uv run --group dev pytest tests/test_comment_health.py tests/test_function_heat.py tests/test_windows.py -q
time uv run --quiet --script .sdlc/comment-health.py
uv run --quiet --script .sdlc/comment-health.py | python3 -c "import sys,json; [json.loads(l) for l in sys.stdin if l.strip()]"
./check.sh
```

What healthy output looks like:

- The tests pass.
- The script exits 0 in well under 60 s. It should take about as long as `function-heat.py` plus a second; if it nears 60, the hot set's blame is the cause.
- It prints about 35 JSON rows: one density row per script file, narration rows for files with comments, five `all scripts` rows, and two rows each for long and hot functions. No row contains comment or source text.
- `./check.sh` is green.
- `uv run --quiet --script scripts/sdlc.py retro`, run read-only, shows a second table under `## Indicators` with `Last retrospective` showing `—` on this first run.

