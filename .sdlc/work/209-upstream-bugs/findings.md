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

Fresh review: skipped, the factory's rounds stand in

## F1. [nit] [correctness] scripts/sdlc.py:~upstream_send: `--send` checks `upstream_info()`'s `available` before it reads the record.

scripts/sdlc.py:~upstream_send: `--send` checks `upstream_info()`'s `available` before it reads the record. A key already `filed` prints its URL only when `gh` is installed and logged in. Without `gh` it returns `filed: null` and the new-issue page instead (R10 says a filed key prints its URL). Checking the record first would be cheap and would match R10 exactly.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F2. [nit] [correctness] scripts/sdlc.py:`_cut_host`: the final safety check looks for each known name anywhere inside a word, so a short slug such as `fix` leaves out a field containing "prefix".

scripts/sdlc.py:`_cut_host`: the final safety check looks for each known name anywhere inside a word, so a short slug such as `fix` leaves out a field containing "prefix". It errs on the safe side, as R6 intends, but it may leave out more than it needs to.

Evidence: reviews/round-1/code.md
Class: code review, round 1
Disposition: minor
Reason: names no path, so it can't be filed as a nit
By: code

## F3. [important] [contract] `_PATH_RE`'s `abs` lookbehind leaves out any absolute path that follows a `:`, and no pattern catches an scp-style remote, so both reach the public body as-is and `_cut_host()` marks them safe.

scripts/sdlc.py:121: `_PATH_RE`'s `abs` lookbehind leaves out any absolute path that follows a `:`, and no pattern catches an scp-style remote, so both reach the public body as-is and `_cut_host()` marks them safe. I checked it with the real `_cut_host()`:

Evidence: scripts/sdlc.py:121
Class: security review, round 1
Disposition: fixed
By: security

## F4. [nit] [contract] `@name` in the person's words or in the output pings that GitHub user when the issue is filed.

scripts/sdlc.py:414: `@name` in the person's words or in the output pings that GitHub user when the issue is filed. Wrap `@` mentions in backticks, or put a zero-width joiner after the `@`, when rendering.

Evidence: scripts/sdlc.py:414
Class: security review, round 1
Disposition: fixed
Reason: weighed S med: handed to the builder's rework, and not raised again
By: security

## F5. [nit] [contract] match `UPSTREAM_MARKER` only on the body's first line, as R12 describes it.

scripts/sdlc.py:7883: match `UPSTREAM_MARKER` only on the body's first line, as R12 describes it.

Evidence: scripts/sdlc.py:7883
Class: security review, round 1
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F6. [nit] [correctness] the triage skill's `Origin: host` instruction has no text test

tests/test_skills.py: the triage skill's `Origin: host` instruction has no text test

Evidence: tests/test_skills.py
Class: test review, round 1
Disposition: recorded
Theme: tests
Cost: S
Value: low
By: test

## F7. [nit] [contract] also turn a dotless ssh-alias remote (`user@alias:path`) into `<remote>`

scripts/sdlc.py:9721: also turn a dotless ssh-alias remote (`user@alias:path`) into `<remote>`

Evidence: scripts/sdlc.py:9721
Class: security review, round 2
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: security

## F8. [nit] [correctness] `_SCP_RE` only matches a dotted host, so `git@localhost:x/y` is not cut, and no test names that boundary

tests/test_upstream.py:417: `_SCP_RE` only matches a dotted host, so `git@localhost:x/y` is not cut, and no test names that boundary

Evidence: tests/test_upstream.py:417
Class: test review, round 2
Disposition: recorded
Theme: robustness
Cost: S
Value: low
By: test

## F9. [nit] [correctness] a two-character owner or config string, like `me`, now turns that word into a placeholder anywhere in the prose.

scripts/sdlc.py:9852: a two-character owner or config string, like `me`, now turns that word into a placeholder anywhere in the prose. The builder said so, and the preview shows it before anything is sent.

Evidence: scripts/sdlc.py:9852
Class: code review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: code

## F10. [nit] [correctness] the one-character-name case, which is never cut, has no assertion, so loosening that rule would go unnoticed

tests/test_upstream.py:443: the one-character-name case, which is never cut, has no assertion, so loosening that rule would go unnoticed

Evidence: tests/test_upstream.py:443
Class: test review, landing round 1
Disposition: minor
Reason: raised by an agent; not weighed or filed
By: test
