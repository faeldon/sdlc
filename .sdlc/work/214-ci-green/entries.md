# 214-ci-green — entries

Retire 2026-11-21-21: taken in by 214-ci-green
Retire 2026-11-21-23: taken in by 214-ci-green

## [2026-11-21-36] [idea] Show a red CI on the base branch in the landing's look and in status

Left undone by 214-ci-green, carried forward when it landed: Say when CI on the base branch is red, in a landing's look or in `status`, so the local gate isn't the only word (the intent's third open question; a seed of its own).
See .sdlc/work/214-ci-green/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-37] [idea] Scan the helpers portable tests call for unencoded reads and writes

Left undone by 214-ci-green, carried forward when it landed: 275 `read_text`/`write_text` calls in non-portable tests and helpers name no encoding. They don't run on Windows today; a test moved into `portable` gets caught by the new check, but a helper it calls doesn't.
See .sdlc/work/214-ci-green/notes.md in its commit.
Raised 2026-11-21.

## [2026-11-21-38] [nit] `_hand_digests` runs `git hash-object` once per call and ignores its stderr.

Raised by the code review of 214-ci-green, round 1: scripts/sdlc.py:3076: `_hand_digests` runs `git hash-object` once per call and ignores its stderr. If it fails, the fallback silently hashes raw bytes, so a git failure could make a record read stale only on the next run. That is safe, but a one-line comment saying so would help.

Theme: docs
Paths: scripts/sdlc.py
Cost: S
Value: low
Raised by: 214-ci-green (correctness)

## [2026-11-21-39] [nit] `_hand_digests` is now a 15-line copy of `sdlc.py`'s, kept the same by hand.

Raised by the security review of 214-ci-green, round 1: plugins/factory/scripts/factory.py:3073: `_hand_digests` is now a 15-line copy of `sdlc.py`'s, kept the same by hand. Pin the two bodies equal in `tests/test_hand_gate.py`, as the repo's other copies are pinned, so a fix to one can't skip the other

Theme: tests
Paths: plugins/factory/scripts/factory.py
Cost: S
Value: med
Raised by: 214-ci-green (contract)

## [2026-11-21-40] [nit] `_lost()`'s new `and not _only_time_wait(port)` branch is proved only by the existing socket test, which exercises it on Linux only.

Raised by the test review of 214-ci-green, round 1: tests/test_factory_ui.py:474: `_lost()`'s new `and not _only_time_wait(port)` branch is proved only by the existing socket test, which exercises it on Linux only. No test combines a refused bind with a stubbed table; the container run is the only proof.

Theme: tests
Paths: tests/test_factory_ui.py
Cost: S
Value: low
Raised by: 214-ci-green (correctness)

## [2026-11-21-41] [nit] the `_hand_digests()` fallback is untested.

Raised by the test review of 214-ci-green, round 1: tests/test_hand_gate.py:145: the `_hand_digests()` fallback is untested. It hashes a path holding a newline with sha256, and covers a failed `hash-object`.

Theme: tests
Paths: tests/test_hand_gate.py
Cost: S
Value: low
Raised by: 214-ci-green (correctness)
