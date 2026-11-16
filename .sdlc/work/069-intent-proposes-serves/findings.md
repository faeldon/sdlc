# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

Skill evals: ran, 1 of 1

## F1. [nit] [correctness] No skill case runs intent with a product doc

The `intent` case's fixture has no `.sdlc/PRODUCT.md`, so the passing run proves only the
no-product path: that the question carries no `serving` clause. The proposal, its `inferred`
mark and the `serving` clause are pinned by the skill's text alone
(`test_intent_proposes_what_a_change_serves_and_its_gate_names_it`), never by a run that shows
intent asks no outcome question and names the outcomes at its gate.

Evidence: evals/intent/scaffold.sh:3, tests/test_skills.py:1145
Class: a skill behaviour pinned by its wording, not by a case that runs it; spec's `serves:` paragraph is the same
Disposition: recorded
