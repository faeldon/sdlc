# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.
>
> Skill evals: ran, 1 of 1
>
> cases-2026-11-16-1: setup scored 1.0 ($0.15), its first run.

## F1. [nit] [cost] cmd_readiness's docstring wraps mid-sentence

The docstring's last sentence breaks after "`drift` has nothing in" and runs a short line, left
from an edit, so it reads as two fragments.

Evidence: scripts/sdlc.py:7543
Class: prose left ragged by an edit in place
Disposition: fixed

## F2. [nit] [context] notes.md doesn't record the fixture's missing CLAUDE.md

Spec R9 lists "its one-line `CLAUDE.md`" in the set-up fixture; the plan dropped it (a
`CLAUDE.md` under the plugin's tree risks `claude plugin validate --strict`, and `AGENTS.md`
alone serves `context` and `docs.policy`), but the notes' departures section doesn't say so, so
the spec reads as unmet.

Evidence: .sdlc/work/058-setup-stops-when-complete/notes.md:9, evals/fixtures/set-up/change/
Class: a departure from the spec recorded in the plan but not the notes
Disposition: fixed
