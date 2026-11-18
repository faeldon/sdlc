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

## F1. [important] [context] The *Retrospectives* paragraph says retro "runs the host's `retro.evidence` and `retro.indicators` (`_evidence()`, the only place they run)".

AGENTS.md:138: The *Retrospectives* paragraph says retro "runs the host's `retro.evidence` and `retro.indicators` (`_evidence()`, the only place they run)". `retro.test_times` now runs through `_evidence()` too, so the sentence is false. The spec says to fix it at ship, but the diff leaves it stale. Edit it to "runs the host's `retro.evidence`, `retro.indicators` and `retro.test_times` (`_evidence()`, the only place they run)".

Evidence: AGENTS.md:138
Class: code review, round 1
Disposition: fixed
By: code

## F2. [nit] [correctness] `_times()` returns an `ok` state with `median: None` when every case is skipped or untimed.

scripts/retro.py:182: `_times()` returns an `ok` state with `median: None` when every case is skipped or untimed. The skill's prose doesn't say what `slow` does then. It is harmless, since `slow` is empty.

Evidence: scripts/retro.py:182
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F3. [nit] [correctness] `drifted_tests` writes its `last` key as `kind(path) == "tests"`.

scripts/indicators.py:441: `drifted_tests` writes its `last` key as `kind(path) == "tests"`. A path that is both under `skip` and a test is already dropped by `_files`, so this is fine. A comment saying so would help.

Evidence: scripts/indicators.py:441
Class: code review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F4. [nit] [correctness] the `# fmt: skip` blocks keep hand-aligned dicts.

tests/test_retro.py:1668: the `# fmt: skip` blocks keep hand-aligned dicts. This is a style choice, not a defect.

Evidence: tests/test_retro.py:1668
Class: test review, round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test

## F5. [nit] [correctness] `lookback or _lookback(home, trunk)` treats an empty-but-given value as absent.

`scripts/retro.py:1046`: `lookback or _lookback(home, trunk)` treats an empty-but-given value as absent. A tuple is always truthy here, so it is harmless, but `if lookback is None` states the intent.

Evidence: scripts/retro.py:1046
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F6. [nit] [correctness] the wrapped line `run), so \`retro\` is` is short.

`AGENTS.md:139`: the wrapped line `run), so \`retro\` is` is short. Rewrapping would read better.

Evidence: AGENTS.md:139
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F7. [nit] [correctness] `lookback or _lookback(...)` would read better as `if lookback is None`.

scripts/retro.py:1046: `lookback or _lookback(...)` would read better as `if lookback is None`. This repeats the earlier F5.

Evidence: scripts/retro.py:1046
Class: code review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F8. [nit] [correctness] the wrapped line `run), so \`retro\` is` is short and could be rewrapped.

AGENTS.md:139: the wrapped line `run), so \`retro\` is` is short and could be rewrapped. This repeats the earlier F6.

Evidence: AGENTS.md:139
Class: code review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F9. [nit] [correctness] the commands-`sdlc.py`-runs line now runs past the wrap width.

docs/REFERENCE.md:103: the commands-`sdlc.py`-runs line now runs past the wrap width.

Evidence: docs/REFERENCE.md:103
Class: code review, landing round 2
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code
