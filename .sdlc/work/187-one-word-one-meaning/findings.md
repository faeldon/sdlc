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

Skill evals: ran, 6 of 7; environment: ship-behaviour; run: .sdlc/reports/cases-2026-11-20-1
Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] The same two decisions are listed twice, as D1/D4 (R11 against R23) and D2/D5 (the `, passed`/`, failed` text on the card).

.sdlc/work/187-one-word-one-meaning/decisions.md:34: The same two decisions are listed twice, as D1/D4 (R11 against R23) and D2/D5 (the `, passed`/`, failed` text on the card). D3 also has its reworded-docs list missing from the ledger line itself. Collapse the duplicates and keep D3's list under its line.

Evidence: .sdlc/work/187-one-word-one-meaning/decisions.md:34
Class: code review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: code

## F2. [nit] [correctness] the phrasing fixture's `# fmt: skip` list packs several phrasings per line, which makes a future edit harder to read

tests/test_feature_map.py:273: the phrasing fixture's `# fmt: skip` list packs several phrasings per line, which makes a future edit harder to read

Evidence: tests/test_feature_map.py:273
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F3. [pre-existing] [correctness] four `test_close_output_is_unchanged` cases (shipped, dropped, rerun, pushed) fail here.

tests/test_archive.py:2642: four `test_close_output_is_unchanged` cases (shipped, dropped, rerun, pushed) fail here. They also fail on a plain extract of the base commit `1829d95`, so this change did not cause them. It is the failure recorded in `build/land-1.gate.md`; the `gh` fixture looks like the cause (that record shows a real `gh` scope error), but I did not confirm it.

Evidence: tests/test_archive.py:2642
Class: behaviour review, landing round 2
Disposition: recorded
By: behaviour
