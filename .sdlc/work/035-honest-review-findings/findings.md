# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:` and `Reason:` lines, counts them into the
> `Sdlc-Findings` trailer, and `ship` refuses while one is still `open`.

## F1. [important] [correctness] Ship's Step 0 still calls `base` its one write before the WAIT

Step 3 now writes `findings.md` before the WAIT too, so Step 0's sentence is false, in the skill
that is the plugin's main promise about what runs without asking.

Evidence: skills/ship/SKILL.md:67
Class: a claim of "the one" or "the only" left stale by an addition; AGENTS.md and REFERENCE.md were updated, this sentence wasn't
Disposition: fixed

## F2. [nit] [cost] The undone-items comment now sits above the findings refusal in cmd_ship

The new block went in between the comment "An undone item that lands as-is is never read again"
and the `open_items()` call it explains.

Evidence: scripts/sdlc.py:2191
Class: a comment detached from its code by an insertion; no other instance in the diff
Disposition: fixed
