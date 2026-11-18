VERDICT: PASS

The kept change was made. `scripts/board.py:843` now says "its agent is resolving a conflict". The same wording is in `tests/test_board.py:1216` and `:1424`. The board paragraph at `docs/REFERENCE.md:579` now says "whose agent is resolving the conflict". No "builder is resolving" wording is left.

## Notes
- Done well: the user-facing string, both test expectations and the reference doc now use the same neutral "agent" wording, so no card names an agent that isn't running.
- I ran no tests. I read `build/round-2.gate.md`, which ends with plugin validation passed. I checked the wording with grep only.
