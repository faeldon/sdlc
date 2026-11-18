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

## F1. [nit] [correctness] tests/test_registry.py:~130: `test_main_runs_a_stand_in_handler` passed before the move, as the plan's "As built" says, so it guards R7 rather than driving it.

tests/test_registry.py:~130: `test_main_runs_a_stand_in_handler` passed before the move, as the plan's "As built" says, so it guards R7 rather than driving it. Stubbing a command that goes through a module, such as `close`, would pin more of it.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [important] [correctness] `HELPERS` leaves out `Command`, the class the registry stores in `COMMANDS` and that `_parser` and `command` depend on.

tests/test_registry.py:25: `HELPERS` leaves out `Command`, the class the registry stores in `COMMANDS` and that `_parser` and `command` depend on. `plan.md`'s "As built" says it is pinned by `test_the_registry_copies_match`, but nothing pins it. Add `"Command"` to `HELPERS`. `COMMANDS` and `HELP_ORDER` differ per script, so they stay out. Without this, a change to one copy of `Command` in `sdlc.py` passes R12.

Evidence: tests/test_registry.py:25
Class: test review, round 1
Disposition: fixed
By: test

## F3. [nit] [correctness] `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so).

tests/test_registry.py:104: `test_main_runs_a_stand_in_handler` already passed before the move (the plan says so). It guards R7 and would catch a later regression, but it never failed on the old code. Only the `config` command is stubbed, so an adapter that bound its handler at import time would be caught for that one command and no other. Stubbing one more, such as `status` with the default no-command path, would cover R5's `--all` default through `main()`.

Evidence: tests/test_registry.py:104
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test
