---
id: 118
slug: retro-spend-indicators
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 118 — Retro sees spent talk, spent tool calls and dead tests · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

This spec builds two of the seed's three views, verbosity and tool calls, which both come from
data close already reads. The suite-pruning pass is filed as a seed of its own (R11), because the
pass needs data no host records today: per-test run times, and which code a test exercises.

1. **R1. Close counts the person's words per stage.** `read_events()` gives each `human` event a
   `words` count, the whitespace-separated words of what was typed, and nothing else of the text.
   `summarize()` sums them per stage, and `trailers()` writes `words=` on each `Sdlc-Stage` line
   and on `Sdlc-Totals`.
   - Test `test_words_are_counted_and_no_text_leaves`: a fixture transcript with a typed reply
     gives `words=` on its stage, and no word of it appears in any event or trailer.
2. **R2. Close counts every tool call.** `read_events()` gives a `tool{name, error}` event for each
   `tool_use` block. Its name comes from `_prompt_name()`, so it is the tool, and the program and
   subcommand for `Bash` (`Bash:git:push`). Its `error` is the matching `tool_result`'s `is_error`.
   - Calls in a factory agent's session count with its role, as its tokens do.
   - `summarize()` keeps, per name, `calls`, `errors` and the count per stage.
3. **R3. Tool calls are written as `Sdlc-Tool` lines.** One line a name:
   `Sdlc-Tool: <name> calls=<n> errors=<n> <stage>=<n> …`, with `tools=` (all calls) on
   `Sdlc-Totals`. `parse_trailers()` reads them into `tools`. A `Close` commit without `tools=`
   is read as unrecorded, never as no calls, the rule `prompts=` already follows.
   - Test `test_tool_lines_round_trip`: `trailers()` then `parse_trailers()` gives back each
     name's counts.
   - Test `test_a_close_from_before_tool_lines_is_unrecorded`.
4. **R4. Comments are counted from a change's diff.** `indicators.comment_lines(diff_u0, markers)`
   counts the added lines of a `git diff -U0` whose stripped text starts with a line-comment
   marker for its file's suffix: `#` for `.py .sh .toml .yaml .yml .rb`, `//` for
   `.js .ts .go .rs .java .c .h .cpp .swift .kt`, `--` for `.sql .lua`, and `<!--` for `.html`.
   Markdown and other prose files are never counted as comments. A suffix with no marker is
   counted under `unknown_lines`, never guessed.
   - Test `test_comment_lines_by_suffix`, on fixed diff text, includes a `#` inside a Python
     string, which is counted by design: the rule is per line, not a parser.
5. **R5. Retro's report gains a `spend` block.** For each closed change in the window it lists the
   change's tier, its added code lines, its comment lines and their share, its agent `out` tokens
   and the person's `words` per stage, and its tool calls and errors.
6. **R6. `spend` names the outliers.** Per tier, it gives the median comment share, `out` tokens
   per added code line, and tool calls per added code line. It names each change at more than
   twice its tier's median on any of them, with which measure and by how much. A tier with fewer
   than 3 changes gives no median and no outlier.
   - Test `test_spend_names_a_change_twice_its_tier_median` on fixed records.
   - Test `test_a_tier_with_two_changes_names_no_outlier`.
7. **R7. `spend` ranks the tools.** Across the window, for each tool name: calls, errors, the
   error share, and the changes it was called in. The ten most-called names and the ten with the
   most errors are listed.
8. **R8. Missing data is said, not zeroed.** A change whose `Close` commit has no `tools=` or no
   `words=` (closed before this change, or with `metrics.transcripts` off) is listed with
   `recorded: false` and left out of every median. `spend` says how many were left out and why.
9. **R9. The retro skill reads `spend`.** `skills/retro/SKILL.md` names the block where it weighs
   the evidence, and `templates/retro.md` gains a `## Spend` section rendered by `render_report()`.
   That is a heading the script now reads, so it gets its `TEMPLATE_READS` entry, and a host's
   override without it is reported under drift's `breaking`.
10. **R10. `docs/REFERENCE.md` describes it.** *Metrics* gets `words=`, `Sdlc-Tool` and `tools=`,
    and *Retrospectives* gets the `spend` block.
11. **R11. The pruning pass becomes a seed.** At ship, this change files a seed in the register for
    the suite-pruning pass, carrying 2026-11-12-2's third bullet in its own words. It goes through
    `/sdlc:idea`'s path (`inbox-commit`), never on this change's branch.

## Design

**Close (`scripts/metrics.py`).**
- `read_events()` already walks every `tool_use` block (it builds `uses`, and the `edit`, `plan`
  and `Skill` events) and every `tool_result` (`is_error` for checks and dialogs). R2 adds one
  event at the `tool_result`, where both the name and `is_error` are known. A call with no result
  (an interrupted turn) counts with `error` unset.
- `words` is `len(text.split())` on the typed entry `_reply_class()` already reads.
- `summarize()` adds per stage a `words` sum and a `tools` dict, and a summary-level `tools` dict.
- `trailers()` writes the new fields. `parse_trailers()` takes `key == "tool"`, as it takes
  `prompt`.

**Retro (`scripts/retro.py`, `scripts/indicators.py`).**
- `indicators.comment_lines()` is pure. Its marker table is a module constant, `COMMENT_MARKERS`,
  named in the module's docstring.
- The diff comes from a `_change_diff(home, rec)` beside `_change_rows()`, with the same base:
  `git diff -U0 --no-renames <base> <sha>`, or `diff-tree -U0` with no base.
- Added code lines come from `_change_rows()` and `_kind()`, so tests and docs never count as
  code.
- `_spend(changes, home, cfg)` builds the block from each change's `metrics` (already parsed by
  `closed_changes()`) and its diff. `retro()` adds it as `"spend"`.

**Report.** `render_report()` fills `## Spend` with two tables: the outliers by tier, and the top
tools by calls and by errors.

## Contracts touched

- **The metrics trailers are a contract, extended and never redefined.** `words=`, `tools=` and
  `Sdlc-Tool` are new keys. No field changes meaning, and a commit without them reads as
  unrecorded (R3, R8), the way `prompts=` was added.
- **No message text, file path or session id leaves `read_events`.** `words` is a count. A tool
  name is `_prompt_name()`'s, names only, never an argument or path (R1's test).
- **`metrics.py` and `indicators.py` are pure.** The new functions take text and records. Git
  runs in `retro.py`.
- **Measuring never refuses.** A transcript the reader can't read still gives
  `Sdlc-Coverage: none: …`, and the new fields are simply absent.
- **`retro` is read-only but for its report.** `spend` reads history only. R11's seed is filed by
  ship, never by `retro`.
- **A change's own numbers print only with `--metrics`.** `spend` is a window summary, built from
  the full records first. Per-change rows go in the report, as the other process views' do.
- **`TEMPLATE_READS` / drift's `breaking`.** `## Spend` is a new heading the script reads in
  `templates/retro.md`, registered in the same change (R9).
- **Release, publish and measuring never read the register.** Untouched.
- **Windows.** The new git call goes through `sdlc._git`, and no platform module is imported.

## Alternatives rejected

- **The pruning pass in this change.** Slowest-first needs per-test times, which `./check.sh -q`
  doesn't print and a host's gate may not give. "Its code was rewritten" needs a map from test to
  code that only a language-aware tool has, and "a newer test repeats it" is a judgment for the
  model, not a count. Each needs a design of its own, so R11 files it.
- **What a call "led to" beyond its error.** An edit kept or reverted would need each edit's path
  matched against the final diff, and `read_events` lets no path out. Errors and rejections are
  what the transcript says for certain, so the report reads a high error share as spent calls.
- **Counting docstrings as comments.** That needs a parser per language. The line-marker rule is
  the same for every host, and its limits are said in the docstring.
- **Words as tokens.** The person's input has no token count in the transcript, only text. Words
  are a count anyone can check.

## Verification

- `uv run --group dev pytest tests/test_metrics.py tests/test_retro.py tests/test_indicators.py -q`
  (or wherever each is tested now).
- `./check.sh` green, `sdlc.py drift` clean.
- `uv run --quiet --script scripts/sdlc.py retro | jq .spend` from the main checkout shows the
  block, with every change before this one's close at `recorded: false` for tools and words, and
  its comment counts present.
