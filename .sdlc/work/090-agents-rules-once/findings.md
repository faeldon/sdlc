# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Skill evals: ran, 2 of 2 (ship, ship-open-finding; .sdlc/reports/cases-2026-11-17-7)

## F1. [nit] [context] REFERENCE.md's new context-pass sentence leaves a 121-column line

The sentence added to the `docs.context` paragraph runs one line to 121 columns in a paragraph
wrapped at about 100, so the host-facing doc reads ragged where this change touched it.

Evidence: docs/REFERENCE.md:251
Class: a wrap left after an inserted sentence; the round-1 code review raised it too
Disposition: fixed

## F2. [pre-existing] [correctness] `_drop_record()`'s docstring breaks off mid-sentence

The docstring ends "Why not, or", so whoever follows AGENTS.md's pointers into close's
docstrings meets half a rule. It predates this change, which doesn't touch the function.

Evidence: scripts/sdlc.py:4186
Class: a truncated docstring; found by the round-1 code review
Disposition: recorded
