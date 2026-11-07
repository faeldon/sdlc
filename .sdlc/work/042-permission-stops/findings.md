# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, and `By: fresh` on a
> finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings` trailer, and
> `ship` refuses while one is still `open`.

## F1. [nit] [correctness] A prompt answered for a sub-agent's tool isn't read

`read_events` finds prompts in the session's own entries only; `_subagent()` reads a sub-agent's
transcript for its edits and run time, never its `permissionDecision`s. In default mode a
reviewer's or the factory's tool prompts stop the person all the same, and go uncounted, as they
did before this change. R1 says "a tool use the person was asked to allow", any.

Evidence: scripts/metrics.py:287 (`_subagent`, which emits only `subagent` and `edit` events)
Class: one reader of the same entries left behind when another was extended
Disposition: fixed
