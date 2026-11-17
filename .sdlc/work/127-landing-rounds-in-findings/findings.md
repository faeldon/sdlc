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

## F1. [important] [context] it says "Ship, and the factory's `carry`, write `findings.md`".

AGENTS.md:195: it says "Ship, and the factory's `carry`, write `findings.md`". After this diff `land --close` writes it too, so a session would take carry as the factory's only writer. Change it to "Ship, the factory's `carry`, and its `land --close` write `findings.md`, and `sdlc.py` only reads it".

Evidence: AGENTS.md:195
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] `complete` for a landing round is `bool(r["reviews"])`, which is looser than the build rounds' "complete for the depth" test.

plugins/factory/scripts/factory.py:4315: `complete` for a landing round is `bool(r["reviews"])`, which is looser than the build rounds' "complete for the depth" test. It is safe today because the land skill runs `land --close` only after `land-verdicts` says `pass`, but `land --close` doesn't check that itself. A partly reviewed landing round would have its partial findings written. If you want the guard here, use `land_verdict(...)["next"] == "pass"`, or keep the note and say the skill owns it.

Evidence: plugins/factory/scripts/factory.py:4315
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [correctness] plugins/factory/scripts/factory.py:1959 (`write_findings`, reached from `carry`): a rerun of `carry` after a landing has begun drops the `land-<n>` sections, since they carry `By:` roles and carry's rounds are build rounds only.

plugins/factory/scripts/factory.py:1959 (`write_findings`, reached from `carry`): a rerun of `carry` after a landing has begun drops the `land-<n>` sections, since they carry `By:` roles and carry's rounds are build rounds only. The next `land --close` restores them, so nothing is lost unless a commit lands in between. Whether that can happen depends on whether the approve step can rerun after a landing. Worth a line in the README if it can.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F4. [nit] [correctness] notes.md already has the unticked line about `templates/findings.md`'s note, which still names only carry.

notes.md already has the unticked line about `templates/findings.md`'s note, which still names only carry. Ship will need a disposition for it.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F5. [nit] [correctness] its note says "the factory's `carry` writes its agents' findings into it", which is still true but no longer names the landing.

templates/findings.md:4: its note says "the factory's `carry` writes its agents' findings into it", which is still true but no longer names the landing. Adding "and its `land --close` its landing's rounds" would match REFERENCE.md. The template isn't a context doc, so this is optional, and a `templates/` edit needs `sdlc.py record` (the round-1 notes.md line already covers it).

Evidence: templates/findings.md:4
Class: code review, round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
