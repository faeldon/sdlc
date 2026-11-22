# Findings

> What a change's review found, one `## ` section a finding, committed with the change.
> `/sdlc:ship` writes it after every review, and the factory's `carry`, and its landing's rounds,
> write their agents' findings into it; `By:` names who raised one: `fresh` for ship's
> fresh-context reviewer, a factory role (`code`, `test`, …) for an agent, and no line on ship's
> own. A rerun keeps each id, marks one the diff no longer shows `fixed`, and never raises again
> one the person answered `wrong`, `intentional` or `minor`; an agent's `wrong` is its arbiter's,
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

## F1. [important] [correctness] The Hosts section still reads "The scorecard reaches hosts when S14 and S15 build it into the plugin".

docs/RETRO-SCORECARD.md:465: The Hosts section still reads "The scorecard reaches hosts when S14 and S15 build it into the plugin". Both seed ids now point at nothing, and "when … build it" is stale, since the waves have landed. The intent's aim is a framework with no plan ids left in it. Reword it without ids or a future tense, for example "The scorecard reaches hosts by way of the plugin, and each part goes where a host already finds its kind:".

Evidence: docs/RETRO-SCORECARD.md:465
Class: code review, round 1
Disposition: fixed
By: code

## F2. [important] [correctness] docs/RETRO-SCORECARD.md:154,156,481: Three more seed ids and change numbers are left in the prose: "captured (S10, 175)" twice in the Feedback-loop and Landing time bullets, and "(S1)" in the lead-time paragraph.

docs/RETRO-SCORECARD.md:154,156,481: Three more seed ids and change numbers are left in the prose: "captured (S10, 175)" twice in the Feedback-loop and Landing time bullets, and "(S1)" in the lead-time paragraph. They are not `**Status:**` lines, so the Outcome's wording technically spares them. But the Problem names ids that "point at nothing" as the defect, and the plan they refer to is deleted. Drop the parentheticals, keeping the rest of each sentence. This is a Constraints trade-off: the framework text is to stay word for word, apart from the Status lines. Removing the ids is the smaller deviation.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: fixed
By: code

## F3. [nit] [correctness] says "the scorecard work (waves 0–5)", which is now only history, since the waves section is gone from the scorecard.

.sdlc/DIRECTION.md:167: says "the scorecard work (waves 0–5)", which is now only history, since the waves section is gone from the scorecard. It is harmless, but "waves" no longer has a referent in the docs.

Evidence: .sdlc/DIRECTION.md:167
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code
