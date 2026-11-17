- KEPT: code: C1: scripts/board.py:354: `_stopped()` copies `sdlc.factory_stop()` line for line, including the `OSError` branch, the three regexes at lines 62–64 and the `problems` wording. It can return `sdlc.factory_stop(folder)` instead, and `STOPPED_RE`, `NEXT_RE` and `PROBLEM_RE` can then go.

## Notes
I only read the code and the diff, and ran nothing.

- `board.py` already calls `sdlc.*` through its live view of `sdlc.py`'s globals, so `sdlc.factory_stop` is reachable from it.
- `sdlc.factory_stop()` at `sdlc.py:4015` and `_stopped()` at `board.py:354` have the same logic and the same results.
- I did not read the plan or the test, so I haven't checked the "Reused, not re-derived" line or the equality assertion. The finding rests on the two functions matching.
- Not checked: whether anything else in `board.py` or the tests reads the three regexes. A grep showed only `_stopped` using them in `board.py`.
