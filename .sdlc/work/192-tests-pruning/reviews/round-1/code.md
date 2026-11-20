VERDICT: PASS

The setting sits in `[retro]` and matches the key in REFERENCE. The reader test now asserts `command` and `summary`. The gate record shows 3461 passed. The change is 192's `tests-pruning`.

## Notes
- Correctness: `test_paths = ["tests/"]` is in the right section, and the acceptance check in `checks.md` would fail if the line were removed. The `test_hand_gate.py` assertions match what `hand_gate()` returns. The builder showed the test failing with `command` removed and passing with it restored.
- Contract: nothing is deleted, so no coverage is lost. `notes.md` gives a reason for each file, named or current.
- Context: no context doc says anything false after this diff.
- D1 is an open default and I agree with it. `["tests/"]` fixes the `spec` misread and leaves other paths counted as they are now.
- Done well: the follow-up in `notes.md` names the real cause of the noisy drift list. Retro takes a test's code to be every code file its last change touched, so a test edited beside `sdlc.py` or `retro.py` keeps drifting.
- I ran no tests. I read the gate record in `build/round-1.gate.md` and the builder's evidence in `build/round-1.md`.
