# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`.

## F1. [important] [correctness] Answering "fix all N first" or "fix F1" reads as a revise, so ship=fixed can't happen

`metrics._reply()` classes any reply matching `REVISE_RE`, which holds `fix`, as `revise`, and
`happy()` makes ship `no` whenever `sdlc:ship` holds a revise reply. So the new option "fix all 5
first" marks ship as a miss, and a ship rerun after the person typed "fix F1" can never read
`fixed`, which R13 and seed 2026-10-26-6 exist for.

Evidence: scripts/metrics.py:82 (`REVISE_RE` includes `fix`), scripts/metrics.py:861 (`_revised` keys on `revise`), scripts/metrics.py:969 (`ship_fixed` requires `sdlc:ship` not in revised)
Class: a reply class that conflates asking for the review's fixes with reworking the change; `rework()`'s `revise` count (scripts/metrics.py:896) reads the same class
Disposition: fixed
Fix: in `scripts/metrics.py`, add `FIX_RE = ^\s*fix\s+(all\b|F\d)` and have `_reply()` return `fix` for it before `REVISE_RE`, so `_revised()` and `rework()`'s `revise` count leave it out; give a pre-gate `fix` stop the extra-stop kind `fix` beside `revise`; add the classes to the module docstring and tests in `tests/test_metrics.py` (a "fix all 5 first" reply keeps ship `yes`; a rerun after "fix F1" with a fixed finding reads `fixed`)

## F2. [important] [context] The docs that list the extra-stop kinds leave out F1's new `fix` kind

F1's fix added `fix` to `EXTRA_KINDS`, so every `Sdlc-Extra` line now carries `fix=<n>`, but the
reference still spells out the line without it, and the retro skill lists the kinds it reads
without it, so a retrospective never weighs a `fix` stop.

Evidence: docs/REFERENCE.md:722 (the kinds and the `Sdlc-Extra:` format), skills/retro/SKILL.md:96 (the `extra` kinds), skills/retro/SKILL.md:168 (which kinds to weigh)
Class: a trailer extended without the docs that spell it out; F1's own fix introduced it
Disposition: fixed
