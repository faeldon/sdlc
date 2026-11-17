---
id: 118
slug: retro-spend-indicators
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 118 — Retro sees spent talk, spent tool calls and dead tests · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/metrics.py`: `read_events()` gives `human` a `words` count (`_words()`, new) and a
  `tool{name, error, role?}` event per `tool_use` block, in the session and in `_run()` (a
  sub-agent's or a factory agent's session, tagged with its role); the call's `error` is set from
  its `tool_result`'s `is_error`, left None with no result. `_blank_stage()`, `_active()`,
  `summarize()` (per stage `words` and `tools`, totals `words` and `tools`, summary `tools`),
  `history_summary()` (`tools: {}`), `trailers()` (`words=` on `Sdlc-Stage`, `Sdlc-Tool` lines;
  `Sdlc-Totals` carries `words=` and `tools=` through `totals`), `parse_trailers()` (`tool` →
  `tools`). The docstring's event list and trailer notes.
- `scripts/indicators.py`: `COMMENT_MARKERS`, `PROSE_SUFFIXES`, `comment_lines(diff_u0, include)`
  and `spend(rows)` (per-tier medians, outliers, tool ranking), both pure. Docstring.
- `scripts/retro.py`: `_added_diff(home, rec, base)` beside `_change_rows()`; `_spend(home, cfg,
  changes, bases, kind)` builds each change's row from its parsed `metrics` and its diff and hands
  the rows to `indicators.spend()`; `retro()` adds `"spend"`; `retro_report()` computes it too and
  `render_report(template, process, spend=None)` fills `{{spend}}`; `cmd_retro()` prints
  `spend.changes` (a change's own numbers) only with `--metrics`.
- `scripts/sdlc.py`: `TEMPLATE_READS["retro.md"]` = heading `Spend`, placeholder `{{spend}}`.
  Close's `measure` needs nothing: it already writes whatever `trailers()` returns.
- `templates/retro.md`: `## Spend` with `{{spend}}`.
- `skills/retro/SKILL.md`: the `spend` key in Step 0's list, and where the Process pass weighs it.
- `docs/REFERENCE.md`: *Metrics* (`words=`, `Sdlc-Tool`, `tools=`), *Retrospectives* (`spend`).
- `tests/test_metrics.py`: R1–R3. `tests/test_indicators.py`: R4, R6, R7. `tests/test_retro.py`:
  R5, R8, R9 through a git fixture.

Where the build reads the spec its own way (raised as defaults in the build report):

- Added code lines come from the same `-U0` diff the comments do, filtered by `_kind()` to code,
  so one git call gives both; `comment_base` is the code lines a marker can be read in, and a
  suffix with no marker counts in `code_added` but not in the share's base.
- R8's "left out of every median" is applied per measure: a change without `tools=`/`words=` is
  in no call figure, but its comment lines (git's) and its `out` tokens (on older `Close` commits
  too) still count where it has them. Without that, no host has a comment median until three
  changes close after this one, and the git-only view the intent promises is empty.
- `spend.changes` (each change's own numbers) prints only with `--metrics`, as `changes[].metrics`
  does; the medians, outliers and tool ranking always print.

Reused rather than re-derived: `_prompt_name()` for a call's name; `_change_base()` (through
`_change_rows()`) for the diff's base; `_kind()` for which added lines are code; `_lean`-style
stripping for `--metrics`; `parse_trailers()`' `_value()` for the new fields.

## Work order

1. **Words** (R1): `words` on `human`, summed per stage and in totals, written as `words=`.
   Test, then code; the suite stays green.
2. **Tool calls** (R2, R3): `tool` events, summarized per name, `Sdlc-Tool` lines and `tools=`,
   parsed back. A commit without `tools=` stays unrecorded.
3. **Comment counting** (R4): `indicators.comment_lines()` on fixed diff text.
4. **Spend summary** (R6, R7): `indicators.spend()` on fixed rows: medians per tier, outliers at
   more than twice, no median under 3 changes, tool ranking.
5. **Retro's `spend` block** (R5, R8): `_added_diff()`, `_spend()`, `retro()["spend"]`, the
   `--metrics` strip, through a git fixture with one change recorded and one not.
6. **The report** (R9): `## Spend` in the template, `render_report()` fills it,
   `TEMPLATE_READS` entry; the skill's text.
7. **Docs** (R10): REFERENCE.md. Gate.
8. **R11** is ship's: the pruning pass's seed is filed through `/sdlc:idea` (`inbox-commit`) on the
   base branch, never by this build or on this branch. Left for ship in `notes.md`.

## Tests

- R1 `test_words_are_counted_and_no_text_leaves` (test_metrics).
- R2 `test_every_tool_call_is_counted_with_its_error` (test_metrics): names by `_prompt_name()`,
  `is_error` read, a call with no result has no error, a factory role's calls counted.
- R3 `test_tool_lines_round_trip`, `test_a_close_from_before_tool_lines_is_unrecorded`
  (test_metrics).
- R4 `test_comment_lines_by_suffix` (test_indicators): `#`, `//`, `--`, `<!--`, a `#` line inside a
  Python string counted by design, Markdown skipped, an unknown suffix under `unknown_lines`, a
  `+++`-looking added line past the header.
- R6 `test_spend_names_a_change_twice_its_tier_median`, `test_a_tier_with_two_changes_names_no_outlier`
  (test_indicators).
- R7 `test_spend_ranks_the_tools` (test_indicators).
- R5, R8 `test_spend_lists_each_change_and_says_what_is_unrecorded` (test_retro): a git fixture,
  one change with `tools=`/`words=` trailers and code comments, one without; `cmd_retro` hides
  rows without `--metrics`.
- R9 `test_the_report_renders_spend` (test_retro); `test_setup_lifecycle`'s existing
  `TEMPLATE_READS` check covers the new entry against the shipped template.
- R10: manual: REFERENCE.md names `words=`, `Sdlc-Tool`, `tools=` and `spend`.
- R11: manual, at ship: the register on the base branch holds the pruning seed.

## Rollback

`git revert` undoes the code. What it doesn't undo: `Close` commits made while this was in carry
`words=`, `tools=` and `Sdlc-Tool` lines, which stay in history. They are additive: every reader
before this one ignores keys it doesn't know (`parse_trailers()` keeps unknown keys, nothing
counts them), so nothing needs undoing. The seed R11 files lives in the register; drop it with
`/sdlc:idea` if the pass is not wanted.
