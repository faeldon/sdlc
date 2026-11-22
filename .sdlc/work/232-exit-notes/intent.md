---
id: 232
slug: exit-notes
tier: 1
impact: patch
stage: shipped
created: 2026-11-22
opened: 2026-11-22T02:22Z
updated: 2026-11-22
shipped: 2026-11-22
idea:
depends_on:
fixes: [2026-11-22-24]
serves: [O3]
origin: self
---

# 232 — An `exit:` line with a note after its code, or a command a hook refused, no longer stops a run

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

From bug 2026-11-22-24: "A behaviour check on 2026-11-22 stopped its run twice on `## Evidence`
lines that did carry an `exit:`, so the mend 215 (2026-11-21-35) made routine could not save it.
The first reply wrote `exit: nonzero (task failed)` for a command whose code it didn't capture,
and `exit: not run (blocked by the guard hook)` for a command the host's PreToolUse hook refused.
The mended reply gave the refused command a number but kept a note after it,
`exit: 2 (hook refusal; the command did not run)`, and `verdicts` read that as missing too. One
mend a role is allowed, so the change stopped for the person with a passing, honest review in hand."

Two gaps:

- **The parser:** `EXIT_RE` (`plugins/factory/scripts/factory.py:320`) is `^\s*exit:\s*\d+\s*$`,
  so any note after the number fails it, though agents annotate by habit.
- **The prompts:** `agents/reviewer-behaviour.md:96` and `agents/builder.md:197` say every command
  carries `exit: <n>`, but not what to do with one a hook refuses, which never ran and has no
  code. A host with a strict guard puts human-only commands in a spec's end-to-end path by
  design, so its behaviour checks meet this on every such change.

## Outcome

- `exit: 2 (hook refusal; the command did not run)` and `exit: 0 # ok` read as exits with their
  code; `exit: nonzero` and `exit: not run` still don't, since they carry no code.
- Both prompts say a command a hook refused is no `$ ` line but goes under the reply's *Not run*,
  with the hook's message, and that every command that ran records its real code
  (`; echo "exit: $?"`), never a word.
- A test drives `verdicts` on behaviour evidence holding `$ <cmd>` then `exit: 2 (note)` and finds
  no problem; the same with `exit: nonzero` still names the missing exit.
- **Moves O3:** a review that ran honestly isn't stopped for its person by how it wrote an exit.

## Affected

- **Area:** the factory's evidence reading and two agents' prompts.
- **Files & components:** `plugins/factory/scripts/factory.py` (`EXIT_RE`, `read_evidence()`),
  `plugins/factory/agents/reviewer-behaviour.md`, `plugins/factory/agents/builder.md`, their
  tests in `tests/test_factory_*.py`; the prompt fixtures if a prompt's text is pinned.
- **Downstream:** every host's factory runs; a behaviour check that wrote a note after its code
  now passes where it stopped.
- **Contracts:** AGENTS.md's evidence rule ("every command with its `exit:` but a read that shows
  its output, which only the script judges") still holds: the script still needs a number; agents
  that judge still have no Write; the one mend a role is unchanged.

## Constraints

- An `exit:` with no number still fails: the code is what the evidence proves.
- The mend stays once a role, and `is_read()` keeps deciding what counts as a read.

## Open questions

- Is `exit: blocked` worth reading as "refused by a hook, no result", or is *Not run* enough?

## Approach

Widen `EXIT_RE` to `^\s*exit:\s*\d+\b.*$` (a code, then anything), and test both forms in the
evidence tests beside 215's. In each prompt's *Evidence* paragraph, add a sentence: a command a
hook refused is listed under *Not run* with the hook's message, never as a `$ ` line, and every
command that ran ends `; echo "exit: $?"` so its code is real.
