---
id: 078
slug: review-escape-classes
tier: 1
impact: none
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-2
depends_on:
serves: [O2]
---

# 078 — Two failure classes for the review doc, from the window's escapes

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The retrospective of 2026-11-17 found three bugs escaped from changes in its window, against none
in the 14 before it (0 of 14 → 3 of 27):

- 2026-11-12-3 from 015;
- 2026-11-12-4 from 047, whose review raised F1 on the bug's own paths and answered it `minor`;
- 2026-11-12-5 from 050, a Tier 1 change whose review had no finding on those paths.

All three, and the Important findings of 049, 052 and 055, sit in how `scripts/metrics.py` reads
transcripts. 041's and 059's Important findings share a second class: a path compared as text
between two sources that write it differently.

Ship's review reads `.sdlc/REVIEW.md`'s "The ways this repo's code fails" as the classes to look
for, and neither is on it. So a review has no reason to ask for a recorded transcript, or to
normalise a path, before it calls a finding `minor`, which is 047's F1 exactly.

## Outcome

- **Moves O2:** the next window's escapes from changes fall back below 3 of 27, with none in the
  two classes named here: M11's second half, which the next retrospective scores, not this change.
- `.sdlc/REVIEW.md`'s "The ways this repo's code fails" holds two new `- **lead**` bullets, as the
  seed words them:
  - **A transcript's shape assumed, not read.** An event `scripts/metrics.py` counts from what a
    spec says the harness writes, not from a recorded transcript: a request counted where its
    outcome decides, a wait taken from agent time the turn never held, two kinds of reply read as
    one. A change to how an event is read carries a test built from a real transcript's entries.
  - **A path compared as text between two sources that write it differently.** `str()` of a `Path`
    against git's POSIX output, or git's quoted path against its `-z` output. Normalise both sides
    first.
- `./check.sh` passes, `tests/test_defaults.py`'s check that each block sits under a guide heading
  and restates none of the guide included.

## Affected

- **Area:** this repo's own review answers.
- **Files & components:** `.sdlc/REVIEW.md` only.
- **Downstream:** `/sdlc:ship`'s review in this repo, and the factory's reviewers when they run
  here. No host reads it; nothing in `defaults/`, `guide/` or `.sdlc/setup.json` changes.
- **Contracts:** AGENTS.md's *This repo's process docs hold only its answers*, and *Nothing about a
  project or a workspace*.

## Constraints

- Both bullets must be true of this plugin's code, not a restatement of `guide/review.md`. The
  second names git's output forms, which any repo can meet, but it is grounded in this repo's
  findings; a general version for every repo would be a guide change, out of scope here.
- Cite changes by id, as the existing bullets do, and name no host.

## Open questions

- ~~The guide says each class here is "pinned by a test the diff should still pass for the right
  reason". Does each bullet name its test? `tests/` may hold a transcript-fixture test for the
  first; the second may have none yet, which would be a seed of its own.~~ Resolved: yes, each
  bullet names the tests that cover its escapes.
- ~~Does the first bullet state "a test built from a real transcript's entries" as something the
  review refuses without, or only as a question it asks?~~ Resolved: a rule, softened to the
  shape of a real transcript's entries (D1).

## Approach

Add the two bullets at the end of "The ways this repo's code fails" in `.sdlc/REVIEW.md`, in the
list's register, naming the test that pins each where `tests/` already has one. Run `./check.sh`.
`sdlc.py ship` deletes seed 2026-11-17-2 through `idea:`.
