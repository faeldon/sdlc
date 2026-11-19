---
id: 166
slug: untestable-none-and-waits
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 166 — A builder's "none" isn't an untestable requirement, and agents wait without sleep · plan

> Written by the builder after reading the code, the intent's Approach being the spec (Tier 1,
> planned since it touches more than a couple of files).

## Files to change

- `plugins/factory/scripts/factory.py`: `UNTESTABLE_RE` refuses an empty answer (`none`, `none.`,
  `n/a`, `na`, any case) with a negative lookahead under a scoped `(?i:...)`, so the pattern stays
  one string. Every reader goes through it: `early_stop()` (the builder report's list, which
  `verdicts` stops on) and `read_step()` (the step record) read alike, with no filter of their own.
- `scripts/factory_records.py`: the same pattern, its pinned copy, so the board's and `status`'s
  `read_step()` read the same.
- `plugins/factory/agents/builder.md`: the untestable paragraph says to leave the line out when
  nothing is untestable; a waiting paragraph after the full-run one in *Then: build it*: never
  `sleep`, give the command its own timeout, or poll in one bounded loop (a `for` loop, since
  `timeout` isn't on every host, macOS included).
- `plugins/factory/agents/reviewer-behaviour.md`: the same waiting paragraph, after its foreground
  rule.
- `plugins/factory/README.md`: the stop-early bullet says an empty answer is no untestable
  requirement.
- `tests/test_factory.py`: each empty spelling doesn't stop `verdicts`; a real one still does.
- `tests/test_board.py`: core's `read_step()` drops an empty answer and keeps a real one (the pin
  test, `test_the_step_record_is_a_pinned_copy`, already compares the two patterns).
- `tests/test_skills.py`: both agents say how to wait without `sleep`.

Reused: `UNTESTABLE_RE` itself (no new helper), the existing `_change`, `_build_report`, `_round`,
`_verdicts` fixtures in `test_factory.py`.

Open questions settled here: **the regex**, not a filter where lines are read, since three readers
(`early_stop()` and both `read_step()`s) use it and the pin test then keeps them agreeing; **the
agent files**, not `common.md` or the build and review prompts, since the agent file is each role's
standing instructions, `common.md` reaches agents that have no Bash, and no recorded prompt copy
(`tests/prompts/*.txt`) then changes.

## Work order

1. Empty untestable answers: the failing tests in `test_factory.py` and `test_board.py`, then the
   pattern in both modules, then the builder's paragraph and the README.
2. Waiting: the failing test in `test_skills.py`, then the paragraphs in `builder.md` and
   `reviewer-behaviour.md`.

## Tests

- `test_factory.py::test_an_empty_untestable_answer_is_no_requirement`: `none`, `none.`, `None`,
  `NONE.`, `n/a`, `N/A.` each leave `verdicts` at its plain next step with `untestable == []`;
  `R3 needs a live GitHub` still stops it.
- `test_board.py::test_the_step_record_drops_an_empty_untestable_answer`: core's `read_step()`
  reads no untestable from `- UNTESTABLE: none.` and one from a real line.
- `test_skills.py::test_the_agents_that_wait_never_sleep`: the builder and the behaviour check
  each say never `sleep`, and name the timeout and the bounded loop.

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, and a run's `runs/step.md`
written before the change reads the same after it but for an empty answer.
