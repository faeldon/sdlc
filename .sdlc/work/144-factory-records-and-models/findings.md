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

## F1. [nit] [cost] `_placeholders()`'s docstring doesn't say it now defuses the scan's shapes

The function now ends by calling `_defused()`, but its docstring still describes only the path
marks and the login name, so a reader of the contract misses the last step; `sdlc.py`'s copy says it.

Evidence: plugins/factory/scripts/factory.py:2791
Class: a docstring left behind by a change to what the function does
Disposition: fixed

## F2. [nit] [correctness] A record quoting a term from `.sdlc/terms.local` is still filed as written

`DEFUSE` covers the scan's `PATTERNS` only; the scan also refuses each regex in the main
checkout's gitignored `.sdlc/terms.local`, so a reply quoting one of those terms still reaches a
landing's gate as written.

Evidence: tests/test_nothing_local.py:120
Class: a second source of refused shapes the filing step doesn't read; nowhere else
Disposition: recorded

## F3. [nit] [correctness] The approver's folder check is a stop with no `runs/stopped.md`

`cmd_agent` returns the folder check as a `problem` after `decision.md` is written; the next
`verdicts` reads the decision as done, so the board and `status` never show the stop, only the
supervisor's report of that one run does.

Evidence: plugins/factory/scripts/factory.py:4110
Class: a stop reported only in the moment, as an agent's `problem` always is
Disposition: minor
Reason: every `problem` from `agent` is reported this way, and `land-check` would still meet the line at the landing's gate; recording it is a change to how problems are kept, not to this check
