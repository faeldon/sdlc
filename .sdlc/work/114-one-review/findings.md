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

Skill evals: ran, 2 of 2

## F1. [important] [correctness] The new test rule contradicts the acceptance-check exception above it

Pass 1 already lets a requirement only a revert could fail be proven by a `checks.md` check
instead of a test; the new paragraph right after it says every requirement's test is named and one
that can't be is a finding, and ship's Step 3 item 1 says the same with no exception. Read
literally, every prose-only requirement proven by an acceptance check (this change's own R3, R4,
R11 and R19) becomes a finding in every host's review.

Evidence: guide/review.md:62, skills/ship/SKILL.md:193
Class: a new rule that drops an exception the text beside it keeps
Disposition: fixed

## F2. [nit] [cost] Two hand-wrapped lines broken in the land skill and AGENTS.md

`plugins/factory/skills/land/SKILL.md`'s Step 0 and Step 3 item 1 each gained a line far past the
100-column wrap the file keeps, and one continuation line of item 1 lost its indent; AGENTS.md:196
runs to 107 columns. They render, but the files are read as text by every session.

Evidence: plugins/factory/skills/land/SKILL.md:64, plugins/factory/skills/land/SKILL.md:138, AGENTS.md:196
Class: prose rewrapped by hand
Disposition: fixed

## F3. [nit] [correctness] bad_bugs says "not one of " with nothing after it

With no severity words (a host whose process doc names none) and a bug proposed with an empty
severity, the reason reads `… is without a severity, not one of ` and stops.

Evidence: plugins/factory/scripts/factory.py:3506
Class: a message built for the case with a list, reached without one
Disposition: fixed
