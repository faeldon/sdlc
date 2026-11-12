# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [important] [correctness] A refused Skill call still counts as the skill starting

The `Skill` tool_use is turned into a `skill` event as soon as it is seen, before its result. A
call the harness refuses (`cannot be used with Skill tool due to disable-model-invocation`, as this
very session's `sdlc:bug` call was) never ran the skill, yet it would close the open gated span in
`summarize()`, and a refused `sdlc:ship` would open a ship stage that never happened.

Evidence: scripts/metrics.py:584
Class: an event counted from the request instead of its outcome; the `check` events already wait
for their tool_result (`checks`, line 528), the pattern to follow.
Disposition: fixed
