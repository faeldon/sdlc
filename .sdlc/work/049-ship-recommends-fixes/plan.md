---
id: 049
slug: ship-recommends-fixes
kind: plan
created: 2026-11-12
updated: 2026-11-12
---

# 049 — Ship's question leads with its recommendation, and a recommended fix is one yes · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `scripts/sdlc.py`: the `fix` disposition, `Fix:` and the `Fresh review:` note in
  `_findings_from_text()`/`findings_entries()`; `COUNTED` for the trailer; `cmd_ship`'s `fix`,
  deep-without-note and `--fixed/--through` refusals; `_and()`, deduped `_issues()`,
  `_question_head()`, `ship_question()`/`cmd_ship_question()` from findings.md; `--fresh-skipped`
  removed; `measure_change` passes `review_fixed`; `_in_change_summary` counts `fixed`.
- `scripts/metrics.py`: `happy()`'s `ship=fixed`.
- `skills/ship/SKILL.md`: Steps 3–7.
- `templates/findings.md`, `guide/review.md`, `docs/REFERENCE.md`, `AGENTS.md`.
- `.sdlc/setup.json`: re-recorded.
- `tests/test_findings.py`, `tests/test_preflight.py`, `tests/test_metrics.py`,
  `tests/test_retro.py`, and `tests/test_risk.py` (its fresh-review question test drove the
  removed `--fresh-skipped`; it now passes the note's value).

## Work order

1. Parsing: `fix`, `Fix:`, the note; `COUNTED`; tests in `test_findings.py`.
2. `cmd_ship` refusals and `--fixed/--through`; tests.
3. The question: `_and`, dedupe, `_question_head`, `ship_question`, `cmd_ship_question`, argparse;
   tests in `test_preflight.py`.
4. Measuring: `happy(review_fixed)`, `measure_change`, `_in_change_summary`; tests.
5. Skill, template, guide, reference, AGENTS; `sdlc.py record`; `./check.sh`.

## Tests

- R1, R3: parse `fix` + `Fix:`; problems for no `Fix:` and for pre-existing; the note's three states.
- R2: `ship` refuses `fix`; the trailer has no `fix` key.
- R3: `ship` refuses a deep diff without the note.
- R4–R7, R9: each question form; each option's presence and absence; the full-clause example
  matches the skill; `fix a finding first` appears nowhere in `scripts/` or `skills/`.
- R8: `--closing 4 --closing 4` reads `#4` once.
- R10: `--fixed` with a finding left `fix`, and a new F6 past `--through`, each refuse, writing nothing.
- R11, R12, R15: `tests/test_skills.py` invariants; manual read of the skill and the guide.
- R13: `happy()` ship `yes`, `fixed`, `no`; `first`/`of` count `fixed`.
- R14: `first_time` counts `fixed`; `ship_fixed`; an old trailer reads as before.
- Manual: this change's own ship asks the new question.

## Rollback

`git revert <sha>` undoes the code, skill and docs. It doesn't undo a host's copy of
`templates/findings.md` made by `/sdlc:setup` (fix forward: a release without it, then
`/sdlc:setup` there). A `findings.md` written with a `fix` line can't be committed, so none reaches
history; `Sdlc-Happy: ship=fixed` trailers written meanwhile stay, and a reverted reader counts them
as neither yes nor no.
