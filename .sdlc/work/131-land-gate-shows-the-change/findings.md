# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry` writes its agents' findings
> into it; `By:` names who raised one: `fresh` for ship's fresh-context reviewer, a factory role
> (`code`, `test`, …) for an agent, and no line on ship's own. A rerun keeps each id, marks one the
> diff no longer shows `fixed`, and never raises again one the person answered `wrong`,
> `intentional` or `minor`; an agent's `wrong` is its verifier's, never the person's, and the same
> fault worded differently is one more. `sdlc.py` reads each heading and its `Evidence:`, `Class:`,
> `Disposition:`, `Reason:`, `By:` and `Fix:` lines, counts ship's own alone into the
> `Sdlc-Findings` trailer (its `agents=` says how many it left out), words ship's question from
> the ones proposed `fix`, and `ship` refuses while one is still `open` or `fix`. On a diff that
> touches a sensitive path, this note also says `Fresh review: ran`, or `Fresh review: skipped,
> <why>`.

## F1. [nit] [correctness] the Step 1 sentence "Under each change, what the yes approves for it…" runs past the ~100-column wrap of the paragraphs around it.

plugins/factory/skills/land/SKILL.md:76: the Step 1 sentence "Under each change, what the yes approves for it…" runs past the ~100-column wrap of the paragraphs around it. Rewrap it.

Evidence: plugins/factory/skills/land/SKILL.md:76
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F2. [nit] [correctness] the question still says "as shown" twice.

plugins/factory/skills/land/SKILL.md:102: the question still says "as shown" twice. It stays, as the intent requires, but a session can't tell that "shown" now means the `preview` text. The skill's Step 2 explains it, so this is only a note.

Evidence: plugins/factory/skills/land/SKILL.md:102
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
