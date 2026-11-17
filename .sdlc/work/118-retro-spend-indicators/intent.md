---
id: 118
slug: retro-spend-indicators
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-12-2
depends_on:
serves: [O4, O5]
---

# 118 — Retro sees spent talk, spent tool calls and dead tests

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

048-architecture-indicators gave `sdlc.py retro` an `architecture` block (`scripts/indicators.py`:
size by kind and tier, hotspots, co-change, growth) and left three parts of 2026-10-24-5 out of
scope. 2026-11-12-2 holds them. Each is something a retrospective can't see today:

- **Verbosity against complexity.** How much a change's code comments say, and how much the human
  and the agent said in its conversation, beside how complex the change is: its diff, its tier, and
  `retro.indicators` where a host has one. A change that commented or talked far more than its size
  needed doesn't stand out. Close already records the conversation's tokens and turns per stage
  (`Sdlc-Totals`, `Sdlc-Stage`), and the comments are in the diff, but nothing sets them side by
  side.
- **Tool calls.** Close names each tool *prompt* on the `Close` commit (`Sdlc-Prompt`), but not
  every call. So no one can say how often each tool is called in a change, by stage (by program
  for a shell call), or what the calls led to (an edit kept, a check run, a finding). Nor which
  calls are most useful and which are spent.
- **A pruning pass for the suite.** The process guide sets each test's lifetime when it is
  written, and ship flags a test that can't fail, but only in the diff it reviews. Nothing looks
  at the tests already in the suite again: one whose code was rewritten, one that repeats a newer
  test, one that now passes for the wrong reason, the slowest. Today's suite is 2,189 tests, and
  `./check.sh` is the gate every factory round waits on, one slot at a time.

## Outcome

- `retro`'s report holds a verbosity view: for each change in the window, comment lines added
  and conversation tokens per stage, beside its diff size and tier. Changes far above their size's
  median are named.
- Close records each change's tool calls by tool, by stage and by program for a shell call, as
  an extension of the metrics trailers, and `retro` sets them beside what they led to.
- `retro` proposes the suite's pruning candidates as a `tests` paydown seed, each with why: code
  rewritten since, a newer test repeating it, the slowest. The person decides which go.
- Each view is pure counting in `indicators.py` or `metrics.py`, pinned by tests on fixed git
  and transcript text.
- **Moves O4:** a retrospective names spent talk, spent calls and dead tests from evidence, not
  impressions.
- **Moves O5:** the suite and the conversations a change costs get smaller where the evidence
  shows they can.

## Affected

- **Area:** the retrospective and close's metrics.
- **Files & components:** `scripts/indicators.py`, `scripts/metrics.py` (the trailer format and
  the transcript reader), `scripts/retro.py` (`_architecture()` or a new block), `scripts/sdlc.py`
  (close's `measure`, `retro`), `skills/retro/SKILL.md`, `docs/REFERENCE.md` (*Metrics*,
  *Retrospectives*), tests.
- **Downstream:** every host's `Close` commits and retrospectives; `/sdlc:retro`'s report and
  direction doc.
- **Contracts:**
  - The metrics event list and trailer format are extended, never redefined.
  - Measuring never refuses (`Sdlc-Coverage: none: <reason>`).
  - `metrics.py` and `indicators.py` stay pure.
  - `retro` is read-only but for its report.
  - Release, publish and measuring never read the register.
  - A change's own numbers print only with `--metrics`.

## Constraints

- No transcript text leaves the machine or lands in a commit: numbers and names only, as today.
- A host with `metrics.transcripts` off gets the git-only views, and says why the rest are absent.
- The pruning pass proposes; it deletes no test and files nothing without the retro's own
  question.

## Open questions

- ~~Is this one change, or should the spec split the three views into seeds of their own? The
  seed allows it.~~ Resolved: this change builds verbosity and tool calls; the pruning pass is
  filed as a seed of its own at ship (spec R11).
- ~~How is a test's run time measured without a paid or slow run: the gate's own output, or
  `pytest --durations` from a gate record?~~ Deferred with the pruning pass, to its own seed.
- ~~Which outcome counts as what a tool call "led to", and can it be read from the transcript
  alone?~~ Resolved: its error or rejection, which the transcript says for certain (spec R2,
  *Alternatives rejected*).
- ~~Does the verbosity view count comment lines by language, or by a convention a host names?~~
  Resolved: by a line-comment marker per file suffix, the same for every host (spec R4).
