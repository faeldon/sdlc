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

## F1. [nit] [correctness] `scripts/sdlc.py` (`needs_of`): a `mend` stop with no step record at all still shows the plain "rerun to ask an agent again" text.

`scripts/sdlc.py` (`needs_of`): a `mend` stop with no step record at all still shows the plain "rerun to ask an agent again" text. That matches the "nobody is mending it" case, but it doesn't say "mending since".

Evidence: reviews/land-1/code.md
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F2. [important] [context] It says a factory run its supervisor stopped reads `stopped` in place of `quiet`, with each problem on a `⚠` line and the step that moves it on under its title.

docs/REFERENCE.md:655-658: It says a factory run its supervisor stopped reads `stopped` in place of `quiet`, with each problem on a `⚠` line and the step that moves it on under its title. That is no longer true for a `mend` stop that is being mended. `_change_lines()` now prints `mending, ` in place of `stopped, `, and a single `→ the factory is mending the <role>: wait for it` line with no `⚠` problem lines. Add a sentence after it: a `mend` stop its supervisor is mending reads `mending` and `→ the factory is mending the <role>: wait for it`, and stays off Needs you until the mend replies or the agent's 3-hour timeout passes.

Evidence: docs/REFERENCE.md:655-658
Class: docs review, landing round 1
Disposition: fixed
By: docs

## F3. [important] [context] The list of `build` stop texts under `■ Needs you` omits the new need that `needs_of()` produces: `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it`.

docs/REFERENCE.md:671-674: The list of `build` stop texts under `■ Needs you` omits the new need that `needs_of()` produces: `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it`. This is a mend left past the agent's timeout. Add it to the list. The line you edited at about 742 only covers the board's step track.

Evidence: docs/REFERENCE.md:671-674
Class: docs review, landing round 1
Disposition: fixed
By: docs

## F4. [nit] [context] the `stopped: rerun to ask an agent again` text is now shown only after a mend is not running.

docs/REFERENCE.md:672: the `stopped: rerun to ask an agent again` text is now shown only after a mend is not running. A short "(a mend not being run by the supervisor)" would help.

Evidence: docs/REFERENCE.md:672
Class: docs review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: docs

## F5. [nit] [correctness] the Needs-you list sentence now runs far past the wrap width, with `parked past its deadline…` following on the same line as the new text.

docs/REFERENCE.md:678: the Needs-you list sentence now runs far past the wrap width, with `parked past its deadline…` following on the same line as the new text. Rewrapping would read better.

Evidence: docs/REFERENCE.md:678
Class: code review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F6. [nit] [context] docs/REFERENCE.md:~678: the new clause lengthens the line that continues `parked past its deadline: free <resource>`, which now runs well past the file's wrap width.

docs/REFERENCE.md:~678: the new clause lengthens the line that continues `parked past its deadline: free <resource>`, which now runs well past the file's wrap width. Re-wrap it.

Evidence: reviews/land-2/docs.md
Class: docs review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: docs

## F7. [nit] [context] docs/REFERENCE.md:~658: the board's own `→` text is `the factory is mending the <role>: wait for it, or …` (`board.py:748`), longer than the `status` text this line quotes.

docs/REFERENCE.md:~658: the board's own `→` text is `the factory is mending the <role>: wait for it, or …` (`board.py:748`), longer than the `status` text this line quotes. The line is about `status`, so this holds. A word saying the board adds more would remove any doubt.

Evidence: reviews/land-2/docs.md
Class: docs review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: docs
