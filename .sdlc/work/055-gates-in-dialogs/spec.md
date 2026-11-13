---
id: 055
slug: gates-in-dialogs
kind: spec
created: 2026-11-13
updated: 2026-11-13
---

# 055 — Ask every gate's question in a dialog · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. The WAIT step of each of the 17 gated skills (core: intent, spec, ship, close, drop, idea, bug,
   triage, retro, release, publish, setup, uninstall; factory: spec, build, eval, review) asks its
   literal question with `AskUserQuestion`: `question` is the text through `?`, each answer in the
   parentheses an option in the given order, labelled exactly as written, `header` the skill's
   name. `test_every_wait_asks_in_a_dialog` fails when a gated skill's WAIT section doesn't name
   `AskUserQuestion` or its `allowed-tools` lacks it.
2. Every literal question in a WAIT section offers 2–4 answers; the test fails on one with more or
   fewer.
3. Only a chosen `yes` (or a `yes, …` label), or a yes typed in Other, approves. A dismissed
   dialog, an error, an empty answer, or an auto-continue after `askUserQuestionTimeout` is a
   **no**. Each WAIT says so in one shared sentence, pinned by the test.
4. When `AskUserQuestion` is unavailable or refused (non-interactive run, `--permission-prompts
   none`, `dontAsk`), the skill asks the same literal question as text with its answers in
   parentheses and stops: today's behaviour, as the fallback.
5. The draft, diff or list being approved is shown as text before the dialog, as now; no WAIT moves
   content into the dialog.
6. No gate marks an option "(Recommended)". Ship's "first option is your recommendation" stays as
   the script words it.
7. Publish's two questions read `(no / yes)`, so a stray tap never pushes or uploads.
8. Ship's options come from the script: `ship_question()` keeps printing the same line; the skill
   turns its parentheses into options by R1's rule and never adds or rewords one. The existing
   ship-question tests pass unchanged.
9. `metrics.read_events()` turns an `AskUserQuestion` result into an `answer{reply}` event, `reply`
   from `_reply()` on the chosen label (read from `toolUseResult.answers`); an empty, dismissed or
   errored result gives no event. In a gated skill's span `summarize()` gathers answers with typed
   replies, and `close_span()` picks the gate as now (last approval; first stop for the factory's
   build), any other dialog in the span staying a `question` stop. Outside a span a dialog is a
   `question` stop, as now. A test feeds an intent span with a clarifying dialog and a gate dialog
   answered `yes` and gets one `gate` (reply approve) and one `question`.
10. The time between an `AskUserQuestion` call and its result counts like the gap before a typed
    reply (`response` up to `idle_minutes`, else `away`/`blocked`), and never as `agent` time:
    Claude Code's `turn_duration` already leaves it out, so nothing is subtracted (ship's F1). A
    test pins a 40-minute dialog wait in a 2-minute turn as `away`, with `agent` 2 minutes.
11. Close's transcript window (the scan that keeps a close's entries) ends at an approving dialog
    the same way it ends at a typed approval, pinned by a test.
12. `Sdlc-*` trailer keys and their meanings are unchanged: a `Close` commit from before this change
    parses as it did, and `test_metrics`'s existing cases pass untouched.
13. Each `evals/*/graders/asks-the-question.md` keeps `target: last_message`: the cases grant no
    `AskUserQuestion`, so a non-interactive run takes R4's text fallback and ends at the literal
    question, which is what those graders read. (Revised in build: a `trace` regex would pass
    vacuously, since the trace holds the skill's prompt and `preflight --question`'s output, both
    carrying the question.) A scoped `run-cases` before ship records in `findings.md` which path
    the runs took.
14. `docs/REFERENCE.md` (ship's question), `metrics.py`'s docstrings (`_ends_with_question`, the
    event list) and `guide/review.md`'s gate line, where it describes how a gate is asked, say gates
    are asked in a dialog with the text fallback.

## Design

**Skills.** Each WAIT keeps its heading and literal question. After "Ask literally:" (and ship's
"Ask exactly what it prints") goes one shared paragraph:

> Ask it with `AskUserQuestion`: the text through `?` as the question, each answer in the
> parentheses an option in that order, labelled as written, `header` the skill's name. Only a
> chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
> refused is a no. If the tool is unavailable or refused, ask the same text, answers in
> parentheses, and stop.

`allowed-tools` gains `AskUserQuestion` in each (the factory's build has it; its decisions step is
unchanged). The gates already offer 2–4 answers each, so nothing folds into Other; the text answers
("edit it", "revise a requirement", "change one") are options, and the person gives the detail in
Other or the next message, as today.

**Metrics.** `read_events()` already maps tool-use ids to calls (`uses`). On a `tool_result` whose
id is an `AskUserQuestion` call, it reads the entry's `toolUseResult.answers`; a non-empty one emits
`{"ts", "kind": "answer", "reply": _reply(first answer), "waited": seconds since the call}`, and no
text leaves the function. In `summarize()`, `answer` joins the open span's stops like a `human` stop
(`extra`, marked `dialog: True`), or is a `question` stop outside one; `close_span()` makes the
picked stop `gate` and an unpicked dialog stop `question` rather than `extra`. `waited` goes to
`response`/`away`/`blocked` by the same rule as `human`; the turn's own duration already leaves it
out (R10). The existing `question` event at the call is replaced by `answer`, so a dialog is counted
once; an unanswered call counts nothing, as a dismissed prompt does today. `_keep`'s close scan
treats an approving `answer` like a typed approval.

**Evals.** Unchanged: the cases exercise the text fallback, graded on `last_message` (R13).

## Contracts touched

- **A skill's WAIT step (always Tier 2).** What each gate approves and when is unchanged: the same
  literal text and answers, asked in a dialog. R3 makes approval stricter (a timeout never
  approves); R4 keeps today's behaviour wherever a dialog can't be shown.
- **The metrics trailer format: extend, never redefine.** No key changes (R12); the point is the
  opposite, keeping a gate answered in a dialog counted as a gate instead of drifting into
  `question`.
- **One WAIT heading per writing skill.** Unchanged; the test still runs.
- **Narrow `allowed-tools`.** `AskUserQuestion` writes nothing, has no Bash rule, and no mode
  auto-approves it; it adds no write that runs unasked.
- **No message text leaves `read_events`.** `answer` carries a class and seconds only.
- **Nothing public names the agent; nothing local.** Untouched.

## Alternatives rejected

- **A separate `options` output from `preflight --question`.** The parentheses already are the
  script's options; a second channel could disagree with the text, and the line is read by tests
  and graders.
- **A short dialog question with the full wording above it.** Breaks "ask literally", and with it
  the graders and metrics that read the text. A long question wraps; how it reads on a phone is
  checked by hand before ship.
- **A header or tag marking the gate's dialog for metrics.** The position rule (last approval in the
  span) already picks typed gates; one rule for both keeps old and new transcripts comparable.
- **Dialogs for the interview and ship's issue-by-issue questions too.** Those are questions, not
  gates; they can follow on their own. This change is the approvals.
- **No-first on every irreversible step.** Close and release can push too, but their yes is the
  routine path of every change; publish alone is the outward one-way act, and the intent asked for
  it alone.

## Verification

- `./check.sh` passes, with the new tests: `test_every_wait_asks_in_a_dialog` (R1), the 2–4 answers
  test (R2), the approval-sentence test (R3, R4), the publish order test (R7), and the metrics tests
  for gate vs question in a span (R9), the dialog wait clock (R10) and the close window (R11).
- `uv run --group dev pytest tests/test_metrics.py -q`: every existing case unchanged (R12).
- `sdlc.py run-cases 055` (scoped, paid, named by ship rather than run unasked): every
  `asks-the-question` grader passes, and the trace shows whether non-interactive runs take the
  dialog or the fallback (R13).
- By hand, in a session on a phone: one gate (`/sdlc:idea` on a scratch entry) shows as a dialog
  with its options, and choosing `no` writes nothing.
