# 193 — Plan

> Tier 1, its Approach touching more than a couple of files: how it is built, written after
> reading the code.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `raised_decisions()`: after each `- DECISION:` line, read its continuation (a new
    `question_lines()`: the lines under it indented deeper than it, blank lines between them
    included, up to the `- OPTION:`/`- WHY:` run or the first line that isn't deeper), fold them
    into the question's text, one space between, a leading `- `/`* ` bullet dropped, then read
    `sub_lines()` from where the continuation ends. Each raise also carries its first line's text
    alone, so a ledger written before this change (its line holding only that first line) is
    matched, not filed again.
  - `cmd_decisions()`: a raise already in the ledger is matched by its text, as now, by its first
    line alone (the old ledgers), or by the same source, kind, options and why when it has
    options (a resumed agent rewording a decision it already raised: 187's D1/D4, D2/D5). The
    reply holding the first raise is rewritten when the agent is resumed, so only the ledger still
    has it: the match is there, not in `raised_decisions()`.
  - `sub_lines()` is unchanged: `read_ledger()` and `approver_weighing()` read it as before.
- `plugins/factory/scripts/landing.py` (sensitive)
  - `read_only_command()`: grep's long option refused when its name (before `=`) is three or
    more characters and a prefix of `--dereference-recursive` (`GREP_FOLLOWS_LONG`), since GNU
    grep takes any unambiguous prefix. Only stricter.
  - Its docstring: a symlink out is refused only for a word that names an existing path; a
    program that walks the tree itself (grep's recursion) is covered by the grep flags alone
    (nit 2026-11-19-72).
  - `_train_begin()`: the comment says why `checks: []` with a hash is safe when preflight can't
    be read (nit 2026-11-19-71).
- `plugins/factory/skills/land/SKILL.md`: the description names the slow gate at the tip and the
  approver's judgement of changed acceptance checks (idea 2026-11-19-68).
- `AGENTS.md`: nit 2026-11-19-70's two lines are already within the wrap at the base (re-wrapped
  since 185); nothing to change.

Reused: `OPTION_RE`, `WHY_RE`, `RAISED_RE`, `SUPERSEDES_RE`, `sub_lines()`, `sub_text()`.
`factory_records.py` copies only `LEDGER_RE`, which doesn't change.

## Work order

1. A question continued in sub-bullets keeps every line, and its options and why are read
   (bug 2026-11-19-79); an old ledger holding the first line alone is matched, its options filled.
2. A decision re-raised with the same alternatives lands once (nit 2026-11-20-1).
3. grep's long-option prefixes refused (nit 2026-11-19-74).
4. Docstring, comment and description wording (2026-11-19-71, -72, idea -68).

## Tests

- `tests/test_factory.py::test_a_question_in_sub_bullets_keeps_every_line_and_its_options`:
  slice 1, 187's D3 shape.
- `tests/test_factory.py::test_a_ledger_holding_a_question_s_first_line_is_matched`: slice 1,
  ledgers already written.
- `tests/test_factory.py::test_a_decision_reraised_with_the_same_alternatives_lands_once`: slice 2.
- `tests/test_train.py::test_read_only_command` gains `--der`, `--dereference`,
  `--dereference-recursive=x`; `test_read_only_command_passes` gains `grep --directories=skip`
  (a `--d` option that isn't a prefix of the refused one) and `--de` (two characters, which grep
  itself refuses as ambiguous).
- `tests/test_skills.py`: the land description names the slow gate and the approver's judgement.

## Rollback

`git revert` undoes all of it: nothing is written outside the tree. A ledger written by the new
code holds a longer question line, which the old code still reads.
