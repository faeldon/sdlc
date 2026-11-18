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

## F1. [nit] [correctness] on a blocking line, the recommendation the person chooses is written as a non-`KEPT` answer, so `ask --answered` always says `rebuild`.

plugins/factory/skills/decide/SKILL.md:77: on a blocking line, the recommendation the person chooses is written as a non-`KEPT` answer, so `ask --answered` always says `rebuild`. That follows R14 as written, but it may send the person to a rebuild when they simply took the recommendation. A line in the skill could say so, or `ask` could treat a blocking recommendation as kept.

Evidence: plugins/factory/skills/decide/SKILL.md:77
Class: code review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: code

## F2. [important] [correctness] the new `/sdlc-factory:decide NNN` is the only way to answer an escalated change's open decisions and defaults, and the board never names it.

scripts/board.py:636: the new `/sdlc-factory:decide NNN` is the only way to answer an escalated change's open decisions and defaults, and the board never names it. At `test` with `decide D1` pending, the card says "decide D1, then /sdlc:ship, or /sdlc-factory:land…". With only defaults to confirm (`confirm N defaults`, no `decide` ids), line 640 sends it to "/sdlc:ship, or /sdlc-factory:land with the others ready", which skips the confirmation the card says it needs. Make the next step at `test` with open items read `/sdlc-factory:decide NNN`, then ship or land. Keep the "in the factory's supervisor" wording for `build`.

Evidence: scripts/board.py:636
Class: ux review, round 1
Disposition: fixed
By: ux

## F3. [important] [correctness] status's "What needs me" still says "confirm N default(s)" and never says where to do it.

scripts/sdlc.py:4383: status's "What needs me" still says "confirm N default(s)" and never says where to do it. Add `/sdlc-factory:decide NNN` to the hint or to status's next-step line, so the person doesn't have to find the skill.

Evidence: scripts/sdlc.py:4383
Class: ux review, round 1
Disposition: fixed
By: ux

## F4. [important] [correctness] `ask` refuses a change not at `stage: test`, and the skill says "say so and stop".

plugins/factory/skills/decide/SKILL.md:35: `ask` refuses a change not at `stage: test`, and the skill says "say so and stop". It should also say what the person can do instead, for example wait for the run's decision, or answer the supervisor's own blocking questions. The same applies to the refusal for a bad or unknown NNN.

Evidence: plugins/factory/skills/decide/SKILL.md:35
Class: ux review, round 1
Disposition: fixed
By: ux
