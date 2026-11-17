---
id: 084
slug: verifier-matches-by-change
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 084 — The verifier's answer matches its change by more than exact text · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `plugins/factory/scripts/factory.py`: a new `asked_changes(reviews)` numbering a round's changes
  `C1`… in `REVIEWERS` order (any other role after, sorted), each `(role, text)` once, CHANGES
  verdicts only; `ID_RE` and a `_change_lead()` beside `_change_path()`; `read_verified()` resolves
  each answer by id, then exact text, then a unique lead, and counts the resolved changes; the
  verify prompt and the landing's verify prompt both list `- C<n>: <role>: <text>` from
  `asked_changes()`.
- `plugins/factory/agents/verifier.md`: what it's given (numbered changes) and "What you return"
  (open each answer with the id, then the change in its own words), the examples in that shape.
- `plugins/factory/README.md`: the `verified.md` row says an answer opens with its change's id.
- `tests/test_factory.py`: R1-R4's tests, 078's round-1 files as they are among them.
- Unchanged, by design (R5): `KEPT_RE`/`DROPPED_RE`, `scripts/board.py`'s and `scripts/sdlc.py`'s
  copies, and their pins in `tests/test_board.py`, `tests/test_archive.py`, `tests/test_metrics.py`.

## Work order

1. `asked_changes()` and its test (order across roles, one id for a repeated line, PASS verdicts
   left out). Stop point: nothing reads it yet.
2. The resolve step in `read_verified()`, tests first: an id with free words, 078's files with no
   id, and every R4 problem; the existing `test_every_change_is_answered_exactly_once` cases stay
   green unedited.
3. Both verify prompts from `asked_changes()`, with a test that the prompt's ids are the ones
   `read_verified()` resolves (the landing's prompt now lists only CHANGES verdicts' lines, the
   ones its read asks for, in the same order).
4. `verifier.md` and the README row.
5. `./check.sh`.

## Tests

- R1: `test_the_verify_prompt_numbers_each_change_once` — `C1`… in `REVIEWERS` order, a duplicate
  line one id, through `_task()`'s verify prompt.
- R2: `test_an_answer_by_id_takes_the_reviewers_text` — `- DROPPED: code: C1: other words — why`
  reads as the reviewer's change, `verdicts` goes on; `carry` takes a KEPT one's reviewer text.
- R3: `test_078s_first_round_reads_answered_and_dropped` — 078's `code.md` and `verified.md`
  verbatim, read once, dropped, no problem; the exact-text cases already in the file still pass.
- R4: `test_an_answer_that_resolves_wrongly_is_a_stop`, parametrised: `C9` of three; an id of
  another role's change; a lead matching two of its role's changes; a lead matching none; an id
  answer and an exact one for the same change (twice); a change left unanswered.
- R5: `tests/test_board.py`, `tests/test_archive.py`, `tests/test_metrics.py` unedited and green.
- R6: read in review; `test_skills.py`'s agent checks still pass.
- R7: `./check.sh`.

## Rollback

`git revert <sha>` undoes it all: no file outside the repo, no stored file rewritten. A
`verified.md` written with ids after the revert still parses by role for the board and `measure`;
only `read_verified()` would stop resolving its answers, a stop on that run, as before this change.
