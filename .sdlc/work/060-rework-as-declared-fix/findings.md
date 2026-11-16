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
> cases-2026-11-16-2: intent scored 1.0 ($0.23).

## F1. [nit] [correctness] A removed line starting `-- ` reads as a file header

`removed_ranges()` takes any line starting `--- ` as a file's header, but a removed line whose text
starts `-- ` (a SQL, Lua or Haskell comment) prints as `--- …` inside a hunk, switching the path to
its text: that file's later runs are blamed against a path that isn't there, and missed.

Evidence: scripts/indicators.py:103
Class: a line-prefix parser reading content as structure
Disposition: fixed

## F2. [nit] [context] The retro skill's architecture pass ends on a garbled sentence

Rewriting the `rework_common` sentence left "A code file most hotspots' changes had to touch: say
whether that is a boundary missing.", which names no number to read.

Evidence: skills/retro/SKILL.md:165
Class: prose left ragged by an edit in place
Disposition: fixed
