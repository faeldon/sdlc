# 209-upstream-bugs — entries

## [2026-11-21-18] [nit] match `UPSTREAM_MARKER` only on the body's first line, as R12 describes it.

Raised by the security review of 209-upstream-bugs, round 1: scripts/sdlc.py:7883: match `UPSTREAM_MARKER` only on the body's first line, as R12 describes it.

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 209-upstream-bugs (contract)

## [2026-11-21-19] [nit] the triage skill's `Origin: host` instruction has no text test

Raised by the test review of 209-upstream-bugs, round 1: tests/test_skills.py: the triage skill's `Origin: host` instruction has no text test

Theme: tests
Paths: tests/test_skills.py
Cost: S
Value: low
Raised by: 209-upstream-bugs (correctness)

## [2026-11-21-20] [nit] also turn a dotless ssh-alias remote (`user@alias:path`) into `<remote>`

Raised by the security review of 209-upstream-bugs, round 2: scripts/sdlc.py:9721: also turn a dotless ssh-alias remote (`user@alias:path`) into `<remote>`

Theme: robustness
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 209-upstream-bugs (contract)

## [2026-11-21-21] [nit] `_SCP_RE` only matches a dotted host, so `git@localhost:x/y` is not cut, and no test names that boundary

Raised by the test review of 209-upstream-bugs, round 2: tests/test_upstream.py:417: `_SCP_RE` only matches a dotted host, so `git@localhost:x/y` is not cut, and no test names that boundary

Theme: robustness
Paths: tests/test_upstream.py
Cost: S
Value: low
Raised by: 209-upstream-bugs (correctness)
