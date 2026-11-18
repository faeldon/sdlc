# Plan

> Tier 1, written because the Approach touches the script, the land skill and the tests.

## Files to change

- `plugins/factory/scripts/factory.py`:
  - `intent_parts(folder)`: new, `{"title", "problem", "outcome"}` quoted from `intent.md`. The
    title is the `# ` heading less its `NNN — ` prefix; Problem and Outcome are the sections
    as written, stripped, read with the existing `_section()`. 125 has not landed, and its build
    skill reads the intent itself, so there is no reader to share.
  - `land_shown(batch)`: new. It renders, as plain text, what each change's yes approves beyond
    the plain landing: its title, then each check (`name: command`), its cases and their cap,
    each undone note with its disposition (`→ seed: <title>`, `→ <shown>` for a bug,
    `→ dropped: <reason>`), each assumed decision as `D<n>: <text>`, and each `How to recover:`
    line. Each part appears only when the change has it. This is the text the dialog shows.
  - `cmd_land_check()`: each batch and excluded entry gains `intent` (`intent_parts()`), and
    the output gains `shown` (`land_shown(batch)`, None with an empty batch). It stays read-only,
    and `land_question()` is unchanged.
- `plugins/factory/skills/land/SKILL.md`:
  - Step 0 names `intent` and `shown`.
  - Step 1 opens each change with its intent, quoted, then gives the rest as now.
  - Step 2 passes `shown` as the `preview` of the `yes` and `yes, with a fix` options. In the
    text fallback, `shown` is printed right before the question. The question itself is
    unchanged.
- `tests/test_land.py`: the tests below.

## Work order

1. `intent_parts()` and `intent` in `land-check`, tested together.
2. `land_shown()` and `shown` in `land-check`, tested together.
3. The skill's Steps 0–2.

## Tests

- `test_intent_parts_quote_the_title_problem_and_outcome`: unit test on a written intent.
- `test_the_dialog_shows_each_disposition_and_assumed_decision`: a unit test of `land_shown()`
  on a batch with a seed, a bug, a drop, an assumed decision, a check, cases and a recovery
  line, plus a change that has none of them (shown as its title alone).
- `test_land_check_shows_each_changes_checks_cases_notes_decisions_and_recovery` (existing,
  extended): `land-check` gives each change its `intent`, and its `shown` holds the dispositions.
  The bug path through `land-check` is already pinned by `test_a_landing_files_each_approved_bug_once`,
  which this change extends with `shown`.

## Rollback

A plain `git revert`: the change adds output fields and skill text, and writes no data.
