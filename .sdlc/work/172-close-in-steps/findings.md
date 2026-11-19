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

Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] scripts/closing.py:`_close_steps`: the return annotation `list[tuple[str, object]]` could be `list[tuple[str, Callable[[_Close], str | None]]]`.

scripts/closing.py:`_close_steps`: the return annotation `list[tuple[str, object]]` could be `list[tuple[str, Callable[[_Close], str | None]]]`.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] scripts/closing.py:`_step_measure`: `lines = []` in the `except` is assigned and then overwritten on the next line, a leftover from the move.

scripts/closing.py:`_step_measure`: `lines = []` in the `except` is assigned and then overwritten on the next line, a leftover from the move.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [nit] [contract] `measure.errors` holds the raw exception text.

scripts/closing.py:396: `measure.errors` holds the raw exception text. In the plugin's own repo, a child after a handoff passes it up unchanged. It's local stdout only, but if a future reader of the run files puts a path or a line of content in a message, that text lands in close's report, so say in the docstring that the message is meant for the person running close and must never become a trailer

Evidence: scripts/closing.py:396
Class: security review, round 1
Disposition: recorded
Theme: docs
Cost: S
Value: low
By: security

## F4. [nit] [correctness] blank the `plugin=` value in `_normal()` so a release bump doesn't break `test_close_output_is_unchanged`

tests/test_archive.py: blank the `plugin=` value in `_normal()` so a release bump doesn't break `test_close_output_is_unchanged`

Evidence: tests/test_archive.py
Class: test review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
