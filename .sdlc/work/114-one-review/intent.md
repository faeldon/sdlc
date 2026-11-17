---
id: 114
slug: one-review
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-18
shipped: 2026-11-18
idea: 2026-11-17-49
depends_on: [112]
serves: [O6, O4]
---

# 114 — One review checklist and one findings record for ship and the factory

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

**2026-11-17-49:** `/sdlc:ship` and the factory review a change differently, and each misses what
the other checks.

- Ship has a context pass (docs still true), nits weighed and recorded in the register, existing
  faults filed as bugs, acceptance checks, skills' cases and `How to recover:`. The factory has
  none of them, although 103 gave its landing the checks, the cases and the recovery.
- The factory has a test reviewer (do the tests prove the requirements, can they fail), security
  depth, the spec's path run end to end, a verifier that drops false positives, and UI/UX. Ship
  has none of them, but the fresh reviewer on a sensitive path.

In the person's words: "standardize what a review covers and how it is recorded, not how it
runs". Decide it "from the evidence already in history, no experiment": the factory's
`reviews/round-N/` and `verified.md` in each landed factory change's commit, ship's `findings.md`
and `Sdlc-Findings` trailers, the `Sdlc-Totals` on each `Close` (stops; the factory's tokens there
are the supervisor's alone, its agents' in `runs/costs.jsonl`), and the bugs with
`Introduced by:` (the escape rate O6 measures).

## Outcome

- `guide/review.md` holds a keyed checklist of review dimensions, each naming who covers it in a
  ship and in a factory run.
- Each gap is filled where it is cheapest. Likely first: ship's correctness pass asks whether each
  test can fail; the factory gets the context pass and files its nits and bugs.
- Both write `findings.md` in one shape, with `By: <role>`, so the retro can compare them without
  counting a factory review as the person's.
- The design's choices cite the evidence above, change by change.
- **Moves O6:** a factory-built change is reviewed for everything a hand-built one is.
- **Moves O4:** the retrospective can compare the two ways of building from one record.

## Affected

- **Area:** review, in both ways of building.
- **Files & components:** `guide/review.md`, `skills/ship/SKILL.md` and its side files,
  `scripts/sdlc.py` (`findings_entries()`, the findings template), `plugins/factory/agents/*.md`,
  `plugins/factory/scripts/factory.py` (what a run writes, the landing's commit),
  `scripts/retro.py`, `.sdlc/REVIEW.md`, `docs/REFERENCE.md`, tests.
- **Downstream:** every host's review doc (an answer to the guide), every ship and factory run,
  `/sdlc:retro`.
- **Contracts:** a host's review doc is its answers to the guide, read block by block (a new
  guide slot is a `defaults/` prompt and `sdlc.py record`); `Sdlc-Findings` and the metrics
  trailers are a contract, extended and never redefined; a factory review is never counted as the
  person's (`Sdlc-Landed`).

## Constraints

- No experiment: the evidence in history decides.
- How each way runs stays its own: no factory agent added to ship, and no ship pass forced into a
  round.
- A host's existing `REVIEW.md` keeps working, with no edit it didn't ask for.

## Open questions

- ~~Which gaps are filled in this change, and which are filed as seeds of their own?~~ Resolved:
  the checklist, ship's test per requirement, the factory's context pass, one record, the factory's
  nits and pre-existing findings as bugs are filled; the rest become undone notes the landing files
  as seeds (spec R1–R19).
- ~~Does the factory's landing write `findings.md` into the change's commit, or keep its reviews as
  they are and add only the shared record?~~ Resolved: `carry` writes `findings.md` beside the
  rounds, and the landing commits it, still with no `Sdlc-Findings` (spec R7, R10).
