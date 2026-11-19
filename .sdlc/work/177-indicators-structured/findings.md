# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its verifier's,
> never the person's, and the same fault worded differently is one more. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts
> ship's own alone into the `Sdlc-Findings` trailer (its `agents=` says how many it left out),
> words ship's question from the ones proposed `fix`, and `ship` refuses while one is still `open`
> or `fix`. On a diff that touches a sensitive path, this note also says `Fresh review: ran`, or
> `Fresh review: skipped, <why>`. Each of ship's further passes that applies says the same on a
> line of its own: `Security review:`, `Behaviour check:`, `UI review:` and `UX review:`, and
> their findings' `By:` is `ship-security`, `ship-behaviour`, `ship-ui` or `ship-ux`, counted as
> ship's own (`passes=` says how many). A behaviour check that ran ends the file with an
> `## Evidence` section: each command on a `$ ` line, the tail of its output, then `exit: <n>`.

Skill evals: ran, 1 of 1; run: .sdlc/reports/cases-2026-11-19-1

## F1. [nit] [correctness] scripts/indicators.py:~560: `_cells` strips each cell, so a row `name` with leading or trailing whitespace won't round-trip through the report, and its `last` comes back null.

scripts/indicators.py:~560: `_cells` strips each cell, so a row `name` with leading or trailing whitespace won't round-trip through the report, and its `last` comes back null. Strip or reject such names in `host_rows`.

Evidence: reviews/land-1/code.md
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F2. [nit] [correctness] scripts/retro.py:~1660: `_code` puts the command in a code span, but a command containing a newline would break the span across lines.

scripts/retro.py:~1660: `_code` puts the command in a code span, but a command containing a newline would break the span across lines. Collapse whitespace in the span.

Evidence: reviews/land-1/code.md
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [contract] `cmd_retro`'s docstring says "Writes nothing, and reads nothing outside the repo", but with `--report` it now also runs the host's `retro.indicators`, so it could say so as `retro_report`'s docstring does

scripts/retro.py:2527: `cmd_retro`'s docstring says "Writes nothing, and reads nothing outside the repo", but with `--report` it now also runs the host's `retro.indicators`, so it could say so as `retro_report`'s docstring does

Evidence: scripts/retro.py:2527
Class: security review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: security
