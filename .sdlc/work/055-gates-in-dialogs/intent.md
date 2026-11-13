---
id: 055
slug: gates-in-dialogs
tier: 2
impact: minor
stage: shipped
created: 2026-11-13
updated: 2026-11-13
shipped: 2026-11-13
idea:
depends_on:
serves: [O3]
---

# 055 — Ask every gate's question in a dialog

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Every gate in the core plugin is asked as plain text: "Ask literally: `…? (yes / edit it / no)`" in
intent, spec, ship, close, drop, idea, bug, triage, retro, release, publish, setup and uninstall,
and in the factory's spec, build, eval and review. Only the factory's build asks its pending
decisions with `AskUserQuestion` (`plugins/factory/skills/build/SKILL.md:137`). So the plugin's
main moment, the human's approval, is the least prominent thing on screen: one line at the end of a
long draft, with the answers in parentheses.

On a phone it is worse: the suggested answers aren't shown, so the person has to read the
parentheses and type `yes` or `change the tier` by hand. Next to the questions that do come as
dialogs (the factory's decisions, the harness's own), the gates look inconsistent.

## Outcome

- Every WAIT step, core and factory, asks its question with `AskUserQuestion`: the question text
  the skill asks today, unchanged, with the answers in its parentheses as the options. Answers that
  need words ("edit it", "revise a requirement", "change one") go through the dialog's free-text
  "Other".
- Ship's options come from the script, beside the question `preflight --question` already words
  (`ship_question()`), never by hand.
- A dismissed dialog is a **no**. `yes` is never marked "(Recommended)". Publish, which can't be
  taken back, does not offer `yes` first.
- The draft, diff or list being approved is still shown as text before the dialog.
- `scripts/metrics.py` counts a dialog answered inside a gated skill's span as that skill's
  **gate**, not a `question` stop, and reads the choice (approve, revise, fix) from the tool's
  result, so a `Close` commit's `Sdlc-*` gate, question and stop counts mean what they did before.
- Tests fail if a gated skill lacks `AskUserQuestion` in `allowed-tools` or its WAIT asks in text
  alone.
- **Moves O3:** each gate is answered with one tap, in a terminal or on a phone, never by typing an
  answer the skill already offered; stops against the required gates stay measurable, so O3's
  evidence keeps its meaning across the switch.

## Affected

- **Area:** the skills' WAIT steps, transcript metrics, the skills' tests and evals.
- **Files & components:** `skills/{intent,spec,ship,close,drop,idea,bug,triage,retro,release,publish,setup,uninstall}/SKILL.md`;
  `plugins/factory/skills/{spec,build,eval,review}/SKILL.md`; `scripts/sdlc.py` (`ship_question()`,
  `cmd_ship_question()`); `scripts/metrics.py` (`AskUserQuestion` handling, `NOT_PROMPTS`, the
  gated span, `_ends_with_question()`); `tests/test_skills.py`, `tests/test_metrics.py`; the
  `evals/*/graders/asks-the-question.md` graders; possibly `guide/process.md` and
  `docs/REFERENCE.md` where they describe how a gate is asked.
- **Downstream:** every host's sessions (every gate looks and answers differently); the `Sdlc-*`
  trailers on future `Close` commits, which `retro` and the product doc's O3 evidence read beside
  every older one; the `claude plugin eval` cases, whose graders check the run "ended at its WAIT,
  asking its own question".
- **Contracts:** a skill's WAIT step, the plugin's main promise to a host (always Tier 2): what it
  approves and when must not change, only how it is asked. The metrics trailer format: extend,
  never redefine. `allowed-tools` grants without a prompt, but `AskUserQuestion` writes nothing.
  Each writing skill keeps exactly one heading containing `WAIT`.

## Constraints

- Approval stays explicit and per-invocation: a dismissed or unanswered dialog writes nothing, and
  no option approves more than the text question does now.
- History's trailers stay readable as they are; old and new `Close` commits count gates alike.
- The wording stays literal: the dialog carries the text the skill names, so the scripts and
  graders that read it still find it.
- `AskUserQuestion` takes 2–4 options and a header of 12 characters at most: a gate with more
  answers folds them into "Other", never drops one.

## Open questions

- ~~Does `AskUserQuestion` work in `claude plugin eval`'s non-interactive runs, and in a session
  where the harness can't show one? If not, what does the skill fall back to, and how do the
  `asks-the-question` graders recognise a dialog as the run's final question?~~ Resolved:
  undocumented for eval runs, denied or removed headless; the skill falls back to today's text
  question, the cases grant no dialog, so their `last_message` graders read the fallback, and a scoped `run-cases` records which
  happens (spec R4, R13).
- ~~How does metrics tell a gate's dialog from an ordinary clarifying one in the same span (intent's
  interview, the `serves:` question): by position (the last in the span, as with typed replies), or
  by a marker in the question?~~ Resolved: by position, the last approval in the span, the rule
  typed gates already use; other dialogs stay `question` stops (spec R9).
- ~~What does the tool's result look like in a transcript, and how reliably does an option label map
  to approve, revise or fix?~~ Resolved: the entry's `toolUseResult.answers` maps each question to
  the chosen label (or the Other text), read through `_reply()` like a typed reply (spec R9).
- ~~Which option order does each gate use: is `no` first wherever a step can't be undone, or only for
  publish?~~ Resolved: the text's order everywhere, and publish alone reads `(no / yes)` (spec R7).
- ~~Is a long question (triage's, close's with every clause) readable in a dialog on a phone, or does
  the dialog carry a short question with the full wording shown above it?~~ Resolved: the literal
  question, unshortened, checked by hand on a phone before ship (spec Verification).
