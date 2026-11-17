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

## F1. [nit] [correctness] `_listed([])` returns `no reviewer`, so the sentence reads `no reviewer review it in up to 3 rounds`.

plugins/factory/scripts/factory.py:830: `_listed([])` returns `no reviewer`, so the sentence reads `no reviewer review it in up to 3 rounds`. The subject-verb agreement is wrong. An empty reviewer list is allowed by config, so consider wording the empty case as its own clause.

Evidence: plugins/factory/scripts/factory.py:830
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F2. [nit] [correctness] `build_question()` writes `1 round` where the old template wrote `1 rounds`.

`build_question()` writes `1 round` where the old template wrote `1 rounds`. The intent says the sentences stay word for word. `notes.md` already records this change, so it is a known, intentional departure and not a defect.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [correctness] `tests/test_skills.py` (`test_the_script_gates_each_build_before_any_reviewer`) now checks that `", with no gate configured"` appears anywhere in `factory.py`.

`tests/test_skills.py` (`test_the_script_gates_each_build_before_any_reviewer`) now checks that `", with no gate configured"` appears anywhere in `factory.py`. That is a weak pin: a stray string elsewhere would satisfy it. The behaviour is already covered by the `start` tests in `tests/test_factory.py`, so the skill test could be dropped or narrowed.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
