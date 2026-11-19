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

## F1. [important] [context] it gives the look line as `- ESCALATED: look: <why>`, but the approver now writes `- ESCALATED: look: <what to look at> — <why>`.

docs/REFERENCE.md:544: it gives the look line as `- ESCALATED: look: <why>`, but the approver now writes `- ESCALATED: look: <what to look at> — <why>`. Update the line to the new form, and say that the decide question quotes the target.

Evidence: docs/REFERENCE.md:544
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] "a published interface the person hasn't approved" could be read as the qualifier covering "destructive operation" and "secret" too.

plugins/factory/agents/approver.md:44: "a published interface the person hasn't approved" could be read as the qualifier covering "destructive operation" and "secret" too. The next paragraph says those stay looks whatever the spec says, but the sentence itself is ambiguous. Reword it, e.g. "a destructive operation, a secret, or a published interface the person hasn't approved".

Evidence: plugins/factory/agents/approver.md:44
Class: code review, round 1
Disposition: fixed
Reason: weighed S med: handed to the builder's rework, and not raised again
By: code
