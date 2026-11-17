---
id: 115
slug: intent-cases-grader
tier: 1
impact: none
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
fixes: [2026-11-17-75]
serves: [O3]
---

# 115 — The intent cases' grader reads the whole reply

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-75:** the `intent` and `intent-product` cases' `judgment` grader judges the run's last
message. When the model asks its WAIT as plain text in a message of its own (no `AskUserQuestion`
in the case), the judge never sees the draft and the tier before it, and votes FAIL. 096's and
100's ships on 2026-11-17 each failed one case, a different one each run, and passed it on a
rerun, so a paid run's verdict on those two cases can't be trusted either way.

## Outcome

- The `judgment` grader reads every message of the reply, the draft and the tier included, or the
  cases end on one message holding the draft and the question.
- Two runs of each case give the same verdict on the same skill text.
- `tests/test_evals.py` pins what the grader is given (the whole reply), without a paid run.
- **Moves O3:** a ship that runs the skills' cases stops for a real failure, not a flaky one.

## Affected

- **Area:** the skills' cases.
- **Files & components:** `evals/intent/graders/judgment.md`, `evals/intent-product/`, the cases'
  suite file, `tests/test_evals.py`.
- **Downstream:** every ship and landing whose diff calls for the intent cases.
- **Contracts:** the cases are paid runs, never in `check.sh`, CI or `ALLOW_RULES`; a fixture
  change must still pass `check --strict` (`tests/test_evals.py`).

## Constraints

- No change to `skills/intent/SKILL.md` to suit the grader.
- The grader still fails a reply that skips the draft or the tier.

## Approach

Find how `claude plugin eval` hands a grader the transcript, and give the `judgment` grader the
whole reply rather than the last message. If the suite can't do that, make the cases' prompt ask
for the draft and question in one message. Pin what the grader receives in `tests/test_evals.py`,
then run both cases twice, behind ship's prompt, to show they agree.

## Open questions

- Does `claude plugin eval`'s grader input let it read the whole reply, or only the last message?
