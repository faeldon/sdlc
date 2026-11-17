# 115 — Plan

> How the intent cases' `judgment` grader comes to read the whole reply.

## What the suite gives a grader

`claude plugin eval` (2.1.311) gives an `llm` grader a `focus` key: `trace`, `last_message`,
`files`, `mock_calls` or a file, defaulting to `last_message` (the run's last assistant text). A
grader `.md`'s frontmatter is spread into the grader, so `focus: trace` there is read. `trace` is
every message of the run, each serialized: past 24 messages it keeps the first 12 and the last 12,
and past 100k characters it keeps the head and the last 20k. The draft and the question are the
run's last messages, so they are always in what the judge sees.

The Approach's first branch holds, so the prompt stays as it is.

## Files to change

- `evals/intent/graders/judgment.md`, `evals/intent-product/graders/judgment.md`: `focus: trace`,
  and criteria that tell the judge to read the agent's own messages, not the skill's text or a
  tool's output, both of which the trace now holds.
- `tests/test_evals.py`: pin it.
- `docs/CONTRIBUTING.md`, *The skills' cases*: one sentence on which focus a judgment grader uses.

## Work order

1. Test: every `llm` grader in a stop case reads `focus: trace` (red: both read the default).
2. The two graders' frontmatter and criteria (green).
3. The CONTRIBUTING sentence; the gate.

## Tests

- `test_a_judgment_grader_reads_the_whole_reply`: Outcome 3 (the grader is given the whole reply).
  Outcomes 1 and 2 (the same verdict across runs) need the paid runs, behind ship's prompt.

## Rollback

Nothing outside the diff: `git revert` undoes it.
