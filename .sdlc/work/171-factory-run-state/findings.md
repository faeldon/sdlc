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

## F1. [nit] [correctness] AGENTS.md:*Modules loaded by path*: it says only `landing.py` is bound to `factory.py`'s globals, so it now leaves `run_state.py` out.

AGENTS.md:*Modules loaded by path*: it says only `landing.py` is bound to `factory.py`'s globals, so it now leaves `run_state.py` out. R18 leaves this to ship's context check; if ship adds it, it is one clause.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] `_killed_at_its_gate` waits up to 120 s for the gate to start, while the POSIX test it twins waits 60 s; neither is a defect, but the two differ for no stated reason

tests/test_train.py:1830: `_killed_at_its_gate` waits up to 120 s for the gate to start, while the POSIX test it twins waits 60 s; neither is a defect, but the two differ for no stated reason

Evidence: tests/test_train.py:1830
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F3. [important] [correctness] `test_a_killed_train_run_resumes` fails with "the reviewer never started" when run alone on this build.

tests/test_train.py:1773: `test_a_killed_train_run_resumes` fails with "the reviewer never started" when run alone on this build. The same test passes at the merge base, in 79 s. R14 cut its wait from 600 × 0.2 s (120 s) to a 60 s deadline. The failing run took 71 s, so the deadline was hit. The loop's startup here takes about 60 s or more, so the 60 s wait is too tight. It failed once under `-n auto` and once alone, and the gate's one green run does not clear it. Give the wait a margin that this machine's startup fits in, such as 120 s, and keep the 0.05 s poll. Or show that the loop starts faster than that, and why it would not here. The spec's 60 s figure should then be revisited.

Evidence: tests/test_train.py:1773
Class: behaviour review, round 1
Disposition: fixed
By: behaviour

## F4. [nit] [correctness] R14 still says "a `time.monotonic()` deadline of 60 s", but the test and its sibling `_killed_at_its_gate` now use 120 s.

.sdlc/work/171-factory-run-state/spec.md:42: R14 still says "a `time.monotonic()` deadline of 60 s", but the test and its sibling `_killed_at_its_gate` now use 120 s. Change R14 to 120 s, since startup here takes about 60 s.

Evidence: .sdlc/work/171-factory-run-state/spec.md:42
Class: code review, round 2
Disposition: recorded
Theme: docs
Cost: S
Value: med
By: code

## F5. [nit] [correctness] R14 still says a 60 s deadline, but the test and `plan.md` now use 120 s.

.sdlc/work/171-factory-run-state/spec.md:42: R14 still says a 60 s deadline, but the test and `plan.md` now use 120 s. Reword R14 to 120 s so the spec matches the code.

Evidence: .sdlc/work/171-factory-run-state/spec.md:42
Class: test review, round 2
Disposition: recorded
Theme: docs
Cost: S
Value: med
By: test
