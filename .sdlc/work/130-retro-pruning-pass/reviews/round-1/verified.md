- KEPT: code: C1: AGENTS.md:138: the *Retrospectives* paragraph still says `_evidence()` runs only `retro.evidence` and `retro.indicators`, but `_times()` in `scripts/retro.py:191` now runs `retro.test_times` through it too.

## Notes
I read `AGENTS.md`, `scripts/retro.py` (`_times()` and `_tests()`) and the diff stat. I ran no tests. The change isn't in `untouched`: the diff adds the `retro.test_times` path, and the stale sentence describes it.
