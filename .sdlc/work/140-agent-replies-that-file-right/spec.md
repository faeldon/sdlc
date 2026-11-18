---
id: 140
slug: agent-replies-that-file-right
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 140 — An agent's verdict is filed from the reply that holds it, and a reply's shape stops costing a mend · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

What this spec takes as given. Each item is a fact checked in the code, unless it says otherwise:

- `_claude()` (`factory.py`) is the one caller of `claude`. It runs `--output-format json` and
  keeps only the JSON's `result`, the session's last reply. This is the cause of 2026-11-18-26.
- The first-line rule is read in seven places. In `factory.py`: `read_rounds()`,
  `land_verdict()`, `_land_task()`'s scan for the verifier and `read_decision()`. In
  `scripts/board.py`: `_factory()` and `_reviewed()`. In `scripts/sdlc.py`: the metrics read at
  `FACTORY_VERDICT_RE` and `FACTORY_DECISION_RE`. The regexes are pinned by
  `tests/test_board.py` and `tests/test_metrics.py`, but the first-line reading itself is not.
- Not checked, and the plan's first step must check it: in print mode,
  `--output-format stream-json --verbose` writes one JSON event a line. That covers each
  `assistant` message with its `text` blocks, and a `result` event carrying `result`,
  `is_error`, `usage`, `total_cost_usd`, `duration_ms` and `num_turns`. It is also unknown
  whether a background task's notice adds a second `result` event or only more `assistant`
  events. The design reads both shapes. REVIEW.md's *A transcript's shape assumed, not read*
  applies here, so R3's fixture comes from a real recorded stream.

1. **R1.** `factory.py agent` runs `claude` with `--output-format stream-json --verbose` and
   reads the session's replies in order. A reply is each `assistant` event's text blocks joined,
   and each `result` event's `result`, with a `result` that repeats the reply before it counted
   once. A test feeds `_claude()` a stream of two replies and fails if it gets back fewer than
   two, or gets them out of order.
2. **R2.** `agent` files the **last** reply that holds the task's answer. A reviewer's holds a
   `VERDICT_RE` line. The approver's holds a `DECISION_RE` line. The verifier's holds a
   `KEPT_RE` or `DROPPED_RE` line. A builder's or behaviour check's holds an `## Evidence` line.
   The spec-writer's holds frontmatter that `split_draft()` finds. When no reply holds one,
   `agent` files the last reply, as it does now, and that reply then stops the run as it would
   today. `test_a_second_reply_never_replaces_the_verdict` runs the fake `claude`, replying
   `VERDICT: PASS …` and then `My verdict stands.`, and fails unless `reviews/round-1/code.md`
   holds the first reply and `verdicts` moves on.
3. **R3.** A recorded stream from a real session that replied twice, with this machine's paths
   replaced by placeholders, is committed under `tests/fixtures/`. A test reads it through
   `_claude()` and fails if the verdict-bearing reply isn't among the replies it returns.
4. **R4.** A session still fails as it does now when `claude` exits non-zero, when the last
   `result` event has `is_error` set, when there is no `result` event, or when no reply holds
   any text. Then no reply is filed and only the figures are recorded. A line that isn't JSON
   is skipped. The existing `test_a_run_reporting_no_cost_or_failing_still_counts` stays green,
   with the fake now printing stream lines.
5. **R5.** The figures come from the last `result` event. Its `total_cost_usd` is the session's
   total. `usage`, `duration_ms` and `num_turns` are summed over every `result` event in the
   run. A test with two `result` events fails if the tokens are counted once or the cost twice.
6. **R6.** One reader, `opening(lines, regex)`, reads a reply's verdict or decision:
   - A first line that matches is the answer, as now.
   - Otherwise, when every line that matches names the same value, the first such line is the
     answer, and the prose before it stays in the file.
   - Otherwise (no line matches, or the lines disagree) the reply has no answer.

   `- CHANGE:`, `- PREEXISTING:` and `- NIT:` lines are read after the answer's line.
   `read_rounds()`, `land_verdict()`, `_land_task()` and `read_decision()` all read through it.
   `test_a_verdict_after_prose_is_read` feeds each of `preamble()`'s current cases through
   `verdicts` and `land-verdicts`. It fails if `Both kept changes are in the code.\n\nVERDICT:
   PASS` stops the run, or if a decision after a sentence does.
7. **R7.** A reply whose verdict or decision lines disagree, none of them on the first line, is
   still the one shape-stop the run mends. That covers `preamble()`, `decision_preamble()`,
   their land counterparts and `verdict_mend()`, which now mean only this case. The mend is once
   a round for each role, a landing round counting as its own, as now. `VERDICT_MEND` and
   `DECISION_MEND` say the reply holds verdicts that disagree. A reply with no verdict line is a
   `rerun` stop, as now. The existing once-a-round tests are rewritten with disagreeing replies
   and stay green.
8. **R8.** `scripts/board.py` and `scripts/sdlc.py` each read rounds and decisions through a
   copy of `opening()`. `test_board.py` and `test_metrics.py` each run a shared table of cases
   through both their copy and `factory.opening()`, and fail if any answer differs.
9. **R9.** No reviewer agent tells itself to run the gate. Every `plugins/factory/agents/reviewer-*.md`
   and `verifier.md` says three things: the script already ran the base branch's
   `[commands] check`, its record is `build/round-<N>.gate.md`, and nothing is started in the
   background. In particular, `reviewer-code.md`'s "run the repo's tests or gate" becomes "a
   named test, in the foreground", and `reviewer-test.md`'s *The run* reads the gate's record
   for the count and runs only the tests it needs, in the foreground.
   `test_no_reviewer_runs_the_gate_or_waits_in_the_background` fails on a reviewer file that
   says to run the gate, or one that names neither `gate.md` nor the background.
10. **R10.** The text that describes the mend matches R6–R7. That means `AGENTS.md` (*The
    factory*), `plugins/factory/README.md` (*Shown, not said*), `WAYS_TEXT["mend"]`, the build
    and land skills' prose about a preamble, and the board fixture's `stopped.md`. `./check.sh`
    stays green, and `test_skills.py`'s rules hold with no new bash.

## Design

**Reading the stream (`_claude()`).**
- The argv changes from `json` to `stream-json --verbose`.
- `stdout` is split into lines, and each line is parsed as JSON. A line that doesn't parse, or
  isn't a dict, is skipped.
- Replies are collected in order:
  - an `assistant` event's `message.content` items with `type == "text"`, joined with blank
    lines and stripped, kept when not empty;
  - a `result` event's `result` string, added unless it equals the reply before it.
- The function returns `(exit, replies, problem, figures)`. The failure test is R4's and is
  applied to the last `result` event.
- `_figures()` takes the last event's cost and the summed usage, duration and turns (R5).
- The process is still run with `capture_output`, UTF-8 and `errors="replace"`, no shell and
  `stdin` closed, so the Windows rules don't change.

**Choosing the reply (`cmd_agent()`).** A small table, `HOLDS`, maps the task (and, for review
tasks, the role) to a predicate over a reply's text:
- `opening(...) is not None or any(...)` on `VERDICT_RE` for a reviewer's tasks;
- `DECISION_RE` for `approve`, and for `mend --role approver`;
- `KEPT_RE` or `DROPPED_RE` for `verify`, `land-verify` and the verifier's mends;
- `EVIDENCE` for `build`, `fix`, `rework`, `decided`, `resolve`, `land-fix` and a behaviour
  mend;
- `split_draft()` finding frontmatter for `spec`.

The reply filed is `next((r for r in reversed(replies) if holds(r)), replies[-1])`. It goes
through `_placeholders()`, then the existing append, write-over or `_file_draft()` path. A
"holds" test only picks a reply. It never decides what the reply says: `verdicts` and
`land-verdicts` still read the file.

**First or last.** The design files the *last* reply that holds an answer, for two reasons:
- If a wake-up reply restates or changes its verdict ("the check I waited on failed: VERDICT:
  CHANGES"), that is the agent's latest judgment, and the run should act on it.
- Picking the first would file a verdict the agent itself replaced.

In 136's case the last reply held no verdict, so the one before it is filed.

**One reader for the answer (`opening()`).**

```python
def opening(lines, regex):
    """The reply's answer line: (index, match), or None."""
    if lines and (m := regex.match(lines[0])):
        return 0, m
    found = [(i, m) for i, line in enumerate(lines) if (m := regex.match(line))]
    if found and len({m.group(1) for _, m in found}) == 1:
        return found[0]
    return None
```

- `read_rounds()` and `land_verdict()` take `(i, m)` and read findings from `lines[i + 1:]`.
- `_land_task()`'s scan for the verifier reads the same way, so the verifier is asked about the
  same changes `verdicts` sees.
- `read_decision()` reads the decision the same way, and its `RECONSIDER` and `IMPACT` reads,
  which already look at any line, are unchanged.
- `preamble(path)` and `decision_preamble(folder)` become "it holds answer lines, and
  `opening()` reads none", which leaves only disagreement. Their callers, the mend's
  bookkeeping and `runs/mended` are unchanged.
- `_no_verdict()`'s wording stays, so the board's and status's problem text doesn't move.
- The board's `_factory()` and `_reviewed()`, and `sdlc.py`'s metrics read, call their own
  copies, as the plugin boundary requires (R8).

**The reviewer prompts.** These are text edits only. In each `reviewer-*.md` and `verifier.md`,
one paragraph is added near the top, in `reviewer-behaviour.md`'s words, which already say it:
the gate is the script's, its record is `build/round-<N>.gate.md`, and the reviewer reads it
and never runs it again. Next to it goes one line: run nothing in the background, because a
background task's notice wakes the session after the reply and the first reply can be lost.
Tests the reviewer runs are named and run in the foreground.

**Edge cases.**
- A reply holding two identical `VERDICT: PASS` lines reads as PASS.
- A `VERDICT: PASS` on the first line with a `VERDICT: CHANGES` later reads as PASS, as now.
- Two disagreeing lines with neither first: the run mends once, then stops.
- A spec-writer's reply is chosen the same way, so a wake-up note never overwrites a draft.
- A `fix` reply is appended as before, but only the chosen reply.

## Contracts touched

- **The factory's one mended shape-stop (AGENTS.md, *The factory*).** It currently says: "a
  reply missing [`## Evidence`], holding its verdict or decision after a preamble (`preamble()`,
  `decision_preamble()`), or a `verified.md` the script can't read, is the one stop a run
  mends". **This change edits that sentence.** A verdict or decision after prose is read, not
  mended, and the preamble stop narrows to disagreeing answer lines. This overturns the
  first-line rule that bug 2026-11-17-18's test states ("The first-line rule stands"). The
  intent asks for it, and the person approving this spec approves that policy edit. README
  *Shown, not said* changes with it.
- **"Only the script judges a reply; never patch a verdict" (the intent's constraint, and *The
  factory*'s "only the script judges").** The design stays inside it. The script picks which of
  the agent's own replies to file and reads it in place. No reply is rewritten, reordered or
  joined.
- **A mend is once a round for each role (`runs/mended`).** This is unchanged. `mended()`,
  `land_mended()` and the refusal in `cmd_agent()` are untouched.
- **`factory.py agent` is the one place the factory runs `claude`.** This still holds: only
  `_claude()`'s argv and its parsing change.
- **Copies across the plugin boundary, pinned by tests.** `board.py` and `sdlc.py` get copies of
  `opening()`, not imports (`factory.py never imports sdlc.py`, and the board reads with
  copies). `test_board.py` and `test_metrics.py` pin them by behaviour, beside the regex pins
  they already have.
- **Metrics: "extend them, never redefine" (*Metrics*).** The trailer format and event list are
  unchanged. `sdlc.py`'s count now also reads a reply whose verdict follows prose. A file that
  opens with its verdict reads the same, so history's numbers only move for replies that were
  uncounted before. This is an extension, not a redefinition.
- **`is_read()`'s rules are unchanged** (intent's constraint). `read_evidence()` is not edited.
- **The scripts run on Windows.** Stream lines are parsed from the same UTF-8 `capture_output`.
  The committed fixture has `\n` endings and is written with `newline="\n"`. Nothing new is
  imported at module top.
- **Nothing about a project or workspace.** R3's recorded stream has its paths replaced by
  placeholders (`_placeholders()`'s marks), and its prompt and replies use neutral examples, so
  `test_nothing_local.py` passes over it.
- **A transcript's shape assumed, not read (REVIEW.md).** R3 is the guard: the parsing is
  tested against a real stream, not this spec's description of one.
- **Agents that judge have no Write.** No agent's tools change, only their prose.

## Alternatives rejected

- **Read the session transcript from Claude Code's project directory.** It is undocumented and
  local to the machine, its path is built differently on Windows, and it is outside the change's
  worktree. The stream is the documented output of the call the script already makes.
- **Move the verdict line to the top when filing.** This would leave every reader as it is, but
  the filed file would no longer be the agent's reply, which is what "never patch a verdict"
  guards against. A reply filed by hand, or before this change, would still stop.
- **File every reply, joined.** This gives two answer lines in one file, and the reader would
  have to guess between them. Picking one reply keeps the file a single reply.
- **File the first reply that holds an answer.** A verdict the agent later replaced would win.
  See *First or last* in Design.
- **Read the first answer line even when a later one disagrees.** A hedge like "VERDICT:
  CHANGES, unless…" followed by the real verdict would be read as the verdict. Disagreement stays
  a question for the agent, asked once.
- **Take background work away through the agents' tools.** Running in the background is a
  parameter of `Bash`, not a tool that an agent definition can withhold, and taking `Bash` away
  would stop the behaviour check from running the change. The prompt says it, and R2 makes a
  missed instruction harmless.
- **Only make the prompts stricter about putting the verdict first.** Every reviewer already
  reads "The first line is exactly `VERDICT: …`", and in one day the run still had nine mends
  and stops. The fix belongs in the reader.
- **Excuse a missing `exit:` beyond `is_read()`.** The intent's constraint keeps `is_read()`'s
  rules. A read that printed output already owes no `exit:`, and a test run, gate or script
  still does.

## Verification

```bash
./check.sh
uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_land.py tests/test_board.py tests/test_metrics.py
uv run --group dev pytest -q -m portable
```

Healthy output looks like this:
- `./check.sh` ends green: ruff clean, the format check clean, every test passing,
  `claude plugin validate --strict` passing.
- The named tests pass: `test_a_second_reply_never_replaces_the_verdict`, R3's
  recorded-stream test, `test_a_verdict_after_prose_is_read`, the rewritten preamble and
  once-a-round tests in `test_factory.py` and `test_land.py`, the copy pins in `test_board.py`
  and `test_metrics.py`, and `test_no_reviewer_runs_the_gate_or_waits_in_the_background`.
- The Windows-portable subset passes.

The recording for R3 is made once, in the plan's first step, before any parsing code is
written. It is one paid session, run from the worktree, which prints two replies:

```bash
claude -p "<a neutral prompt that starts a short background command and replies VERDICT: PASS>" --output-format stream-json --verbose > /tmp/stream.jsonl
```

Its lines, with paths replaced by placeholders, become the fixture. When it shows a second
`result` event, or none, the fixture proves that the reader takes either shape.

**Boundaries.**
- *Always:* file one of the agent's own replies as written, read answers only through
  `opening()` and its pinned copies, and keep the mend at once a round for each role.
- *Ask first:* any edit to AGENTS.md beyond the mend sentence R10 names, and any change to
  `is_read()` or `read_evidence()`.
- *Never:* rewrite, reorder or join a reply, read a verdict from a reply whose answer lines
  disagree, or have a reviewer run the gate.

