---
id: 140
slug: agent-replies-that-file-right
kind: plan
created: 2026-11-18
updated: 2026-11-18
---

# 140 — An agent's verdict is filed from the reply that holds it, and a reply's shape stops costing a mend · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

What the stream holds was checked first, as the spec's open item asked. One haiku session was run
with `--output-format stream-json --verbose`. It started `sleep 5; echo done` in the background
and replied `VERDICT: PASS`. The stream shows that a background task's notice adds a second
`assistant` text event **and** a second `result` event. The second result's `total_cost_usd` is
cumulative (0.00438, then 0.00478). Its `usage`, `duration_ms` and `num_turns` are that turn's own
(2322 ms and 2 turns, then 954 ms and 1 turn). That confirms R5's split. Each final `assistant`
text equals the `result` after it.

- `tests/fixtures/stream-two-replies.jsonl` (new): that stream, 17 lines. The `system` and
  `rate_limit_event` lines keep only their type, subtype, ids and task fields, because the
  machine's plugin, skill and MCP lists in `init` name local projects. Paths are replaced by
  `<path-to-clone>` and `<home>`. `assistant`, `user` and `result` lines are kept whole.
- `plugins/factory/scripts/factory.py`:
  - `_claude()`: the stream argv's parsing. It returns `(exit, replies, problem, figures)`.
  - `_figures()`: takes the list of `result` events.
  - `cmd_agent()`: argv `stream-json --verbose`. It picks the reply through a new `holds(role,
    reply)`.
  - New `opening(lines, regex)`, read by `read_rounds()`, `land_verdict()`, `_land_task()`'s
    verifier scan and `read_decision()`.
  - `preamble()` and `decision_preamble()` narrow to disagreement.
  - `VERDICT_MEND`, `DECISION_MEND` and `WAYS_WHY["mend"]` get new wording.
  - The `_figures` docstring stops naming `--output-format json`.
  - Reused as they are: `_placeholders()`, `split_draft()`, `_file_draft()`, `mended()`,
    `land_mended()` and `read_evidence()`, which is not edited.
- `scripts/board.py`: `opening()`, a copy, read by `_factory()` and `_reviewed()`.
- `scripts/sdlc.py`: `_factory_opening()`, a copy, read by the decision read in the needs reader
  and by `_factory_files()`.
- `plugins/factory/agents/reviewer-{code,security,test,behaviour,ui,ux}.md` and `verifier.md`:
  each gets the gate-is-the-script's paragraph and the no-background line. The code, test and
  verifier lines that ran tests or the gate now run a named test in the foreground.
- Prose (R10):
  - `AGENTS.md` (*The factory*'s mend sentence)
  - `plugins/factory/README.md` (*Shown, not said*)
  - `plugins/factory/skills/build/SKILL.md` (the stop and mend paragraph)
  - `plugins/factory/skills/land/SKILL.md` (the `mend` line)
  - `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md` (`WAYS_WHY`'s text)
- `tests/fixtures/opening-cases.json` (new): the shared table of `opening()` cases that R8's pins
  read.
- Tests:
  - `tests/test_factory.py`: the fake `claude` prints stream lines. New tests cover R1–R7 and R9.
    The two preamble tests are rewritten with disagreeing replies.
  - `tests/test_land.py`: the `_claude` stand-ins return a list. The landing preamble tests use
    disagreeing replies. A landing verdict after prose is now read.
  - `tests/test_board.py` and `tests/test_metrics.py`: `opening()` copy pins, plus a call-site
    test each (built: `board._factory()`/`_reviewed()` and `sdlc._factory_files()` read an answer
    after prose).
  - `tests/test_skills.py` (built): the build skill's stop paragraph pin now reads "a reviewer's
    verdict lines that disagree", the sentence R10 rewrote.
- Built beyond the list above: `factory.py`'s module docstring, `verdicts`' and
  `land-verdicts`' docstrings and their `mendable` comments, and the README's "what each review's
  first line says" now describe the reading `opening()` does. The spec's `WAYS_TEXT["mend"]` is
  `WAYS_WHY["mend"]` in the code.

## Work order

1. **The stream (R1, R3, R4, R5).** `_claude()` parses lines, collects replies and results, and
   fails as R4 says. `_figures()` sums usage, duration and turns, and takes the last cost.
   `cmd_agent` passes the stream argv and, for now, files `replies[-1]`, which behaves as before.
   The fake `claude` prints an `assistant` line and a `result` line per reply
   (`FAKE_CLAUDE_REPLIES`, a JSON list). Tests: two replies come back in order, the recorded
   fixture, the cost-and-tokens sums, and the existing failure test stays green.
2. **The reply that holds the answer (R2).** `holds(role, reply)`: a verdict line for a reviewer,
   a decision line for the approver, a `KEPT` or `DROPPED` line for the verifier, `## Evidence`
   for the builder, and a bare `---` for the spec-writer. `cmd_agent` files the last reply that
   holds one, else the last reply. Test: `test_a_second_reply_never_replaces_the_verdict`.
3. **`opening()` in factory.py (R6, R7).** The four readers go through it. `preamble()` and
   `decision_preamble()` mean disagreement only, and the mend texts change. Tests:
   `test_a_verdict_after_prose_is_read` (verdicts and land-verdicts), an `opening()` unit table,
   and the preamble and once-a-round tests rewritten with disagreeing replies.
4. **The copies (R8).** `board.py`'s `opening()` and `sdlc.py`'s `_factory_opening()`, each
   called where the first line was read. The pins run `tests/fixtures/opening-cases.json`
   through each copy and `factory.opening()`.
5. **The prompts (R9).** The reviewer and verifier text edits. Test:
   `test_no_reviewer_runs_the_gate_or_waits_in_the_background`.
6. **The prose (R10).** AGENTS.md, the README, both skills, `WAYS_WHY` and the board fixture.
   Then `./check.sh`.

## Tests

- R1: `test_claude_returns_every_reply_in_order` gives the fake two replies and expects both, in
  order. A `result` that repeats its `assistant` text counts once.
- R2: `test_holds_picks_each_role_s_answer` (built: a unit test of `holds()` for each role).
- R2: `test_a_second_reply_never_replaces_the_verdict` runs a `review --role code` whose fake
  replies `VERDICT: PASS …` and then `My verdict stands.`. `code.md` must hold the first, and
  `verdicts` must move on. The same test covers the case with no answer in any reply, where the
  last reply is filed.
- R3: `test_a_recorded_stream_with_two_replies_reads_both` reads the fixture through `_claude()`
  with a stand-in `subprocess.run`. It expects `VERDICT: PASS` among the replies, the wake-up
  reply last, and `holds()` to pick the verdict.
- R4: the existing `test_a_run_reporting_no_cost_or_failing_still_counts`, on the stream fake.
  `test_a_stream_without_a_result_or_with_an_error_fails` covers no `result`, an `is_error` on the
  last result, non-JSON lines skipped, and no text.
- R5: `test_figures_sum_a_session_s_turns_and_take_its_last_cost` uses two `result` events.
- R6: `test_opening_reads_the_answer_line` (a unit table), and `test_a_verdict_after_prose_is_read`
  for a reviewer, the approver and a landing reply.
- R7: `test_a_reviewer_s_disagreeing_verdicts_are_mended_by_the_same_reviewer`,
  `test_an_approver_s_disagreeing_decisions_are_mended_by_the_approver`,
  `test_a_landing_verdict_that_disagrees_is_mended` and `test_a_landing_mend_is_once_a_role_a_round`
  are rewritten. A reply with no verdict is still `rerun`.
- R8: `test_the_boards_opening_is_a_pinned_copy` and
  `test_sdlcs_opening_is_a_pinned_copy_of_the_factorys` run over the shared table.
- R9: `test_no_reviewer_runs_the_gate_or_waits_in_the_background`.
- R10: `./check.sh`, with `test_skills.py`'s rules and the board's `stopped.md` pin (it compares
  the fixture with `WAYS_WHY`).

## Rollback

`git revert` covers it all. Nothing is written outside the repo. Replies filed under the new
reading stay as they were filed, since each one is an agent's own reply. A run that a reverted
reader would read differently (a verdict after prose) stops as `mend` again, which is what it did
before this change.
