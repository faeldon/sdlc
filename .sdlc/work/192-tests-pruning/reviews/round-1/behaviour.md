VERDICT: PASS

## Notes
- The change is a config setting (`retro.test_paths = ["tests/"]`) and one stronger assertion in `tests/test_hand_gate.py`. The spec names no end-to-end command, so I ran the closest path. `sdlc.py config` now reports `test_paths: ["tests/"]`, and `tests/test_hand_gate.py` passes (49 tests).
- The gate record `build/round-1.gate.md` reads `GATE: PASS`.
- `notes.md` gives a reason for every file named in the intent, so the outcome is covered. No test was deleted, so no assertion had to move.
- I did not rerun `retro`. It reads the main checkout's config, so `tests.drifted` shows the fix only once the change lands, as `notes.md` says.
- `checks.md` has one check: "The suite is tests/ alone". I expect it to pass, because the config output contains `"test_paths":["tests/"]` once spaces and newlines are stripped. I did not run it.
- `decisions.md` D1 is a default the builder took and is unanswered. It doesn't block the review, and the chosen option is the smaller one.

## Evidence
$ cat .sdlc/work/192-tests-pruning/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ uv run --quiet --script scripts/sdlc.py config | tr -d ' \n' | grep -o '"test_paths":[^]]*]'
"test_paths":["tests/"]
exit: 0

$ git diff
(diff of .sdlc/config.toml and tests/test_hand_gate.py, as quoted above)
exit: 0

$ uv run --group dev pytest tests/test_hand_gate.py -q
49 passed in 13.72s
exit: 0
