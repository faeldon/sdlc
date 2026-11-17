---
id: 084
slug: verifier-matches-by-change
tier: 2
impact: patch
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea:
depends_on:
reworks: [038]
serves: [O6]
---

# 084 — The verifier's answer matches its change by more than exact text

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

On 2026-11-17 the factory's first real run here, 078-review-escape-classes, stopped after round 1's
verification although its build was green and the verifier's answer was right. The code reviewer
asked for one change, a two-sentence `- CHANGE:` line about the attribution at
`.sdlc/REVIEW.md:50`. The verifier answered it as `- DROPPED: code: .sdlc/REVIEW.md:50: the
attribution of the two tests is wrong, so credit each to the change whose finding it pins. — <why>`:
a correct reason, backed by the `Sdlc-Fixes` trailers, but its own one-line summary of the change
rather than the reviewer's text.

`read_verified()` (`plugins/factory/scripts/factory.py:695-723`) matches each answer to its change by
exact `(role, text)` equality, so `verdicts` reported the reviewer's change answered "0 times, not
once" and the answer naming "a change no review of round 1 asks for", and returned `stop`. The run
halted at `stage: build`, leaving only `/sdlc:ship` by hand.

The verifier is told to answer "in the reviewer's own words after its role"
(`plugins/factory/agents/verifier.md:43`), and the verify prompt hands it each change in full
(`factory.py:1480-1494`), but nothing makes a model copying a long line word for word reliable.
Each such stop costs the person a stop the factory exists to save (O6), on a run with nothing wrong.

## Outcome

- **Moves O6:** a factory run stops on verification only when a change really went unanswered,
  answered twice, or answered with no basis, never because the verifier said what the change was in
  its own words. A run like 078's round 1 carries on: here, to the approver, its one change dropped.
- A test built from 078's round-1 `code.md` and `verified.md`, as the files are, passes
  `read_verified()` with the change answered once and counted dropped, and the verdict rule
  unchanged.
- Still a problem, and still a stop, each pinned by a test: a change left unanswered, one answered
  twice, an answer that names no change of the round, an answer whose role isn't the change's.
- The three readers agree on every line, the board's and `measure`'s copies still pinned to
  `factory.py`'s by tests; a `verified.md` written before this change reads as it did, so history's
  trailers and retro's counts don't move.
- `./check.sh` passes.

## Affected

- **Area:** the factory's review loop, and every reader of its verification file.
- **Files & components:** `plugins/factory/scripts/factory.py` (`read_verified()`, the verify
  prompt, perhaps its patterns), `plugins/factory/agents/verifier.md` ("What you return"),
  `scripts/board.py` and `scripts/sdlc.py`'s copies (`FACTORY_KEPT_RE`, `FACTORY_DROPPED_RE`,
  `scripts/sdlc.py:3636-3673`) if the line's shape changes, and `tests/test_factory.py`,
  `tests/test_board.py`, `tests/test_archive.py`'s verified counts.
- **Downstream:** every factory run's `verdicts` and `rework` (the builder reworks the KEPT lines),
  the approver, `/sdlc-factory:land`'s check, close's `measure` trailers (dropped changes per
  reviewer), the board's round chips, and retro through those trailers; hosts that run the factory,
  whose code it is.
- **Contracts:** the metrics *event list and trailer format are a contract: extend them, never
  redefine*; the factory's copies of `sdlc.py`'s parsing, each pinned by a test; *agents that
  judge have no Write* (the verifier still returns text `factory.py` files).

## Constraints

- No answer that matches nothing may pass: loosening the match must not let a verifier answer a
  change it never read, or one answer cover two changes.
- A wrong DROPPED stays as visible as now: the builder never reworks a change no one kept, and ship
  still reviews the diff.
- `verified.md`'s existing lines keep their meaning for every reader: a new shape is added beside
  the old, never instead of it, and no stored file needs rewriting.
- The script matches; no model judges whether an answer fits its change.

## Open questions

- ~~How is an answer tied to its change: by number (the verify prompt numbers each change `C1`,
  `C2`, …, and the answer names `C1`, its words free), by its `path:line` lead plus role (most
  CHANGE lines open with one), or by a looser text match, the hardest to make safe?~~ Resolved: by
  number, with exact text and then a unique `path:line` lead as fallbacks for answers without one;
  no fuzzy match (spec R2, R3).
- ~~Does numbering need the reviewers' files to change, or can it come from a change's order in the
  round, as `verdicts` already lists them, and can that order shift between the prompt and the
  read?~~ Resolved: from the order `read_rounds()` reads them in, the same for the prompt and the
  read; a verified round's review files don't change (spec R1).
- ~~Should a stop like 078's be resumable, the verifier asked once more with what it got wrong, as
  `mend` does for a missing `## Evidence`, rather than the person shipping by hand?~~ Deferred:
  matching by id removes the cause; a re-ask is a seed of its own.
- ~~078's run found a second gap: `factory.py start` passed a change whose worktree couldn't load
  the factory's agents, its branch predating 079's `enabledPlugins`. Here, or in seed
  2026-11-17-7's write-up?~~ Deferred: out of this change's scope, for seed 2026-11-17-7's
  write-up.
