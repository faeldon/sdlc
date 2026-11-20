VERDICT: PASS

The change's only behaviour edits are in `scripts/retro.py`, and both behave as the intent says.

- `_last_experience` now reads a hand-edited rating cell without raising. A cell of `abc`, `7`, `2.5` or `—` reads as no rating, and `3` and `3.0` read as 3.
- `_experience_text` now passes `rating` and `before` through `_num` in its table row. The 21 experience tests in `tests/test_retro.py` pass.

## Notes
- There is no `checks.md` for this change, so there is nothing to read or predict.
- The spec names no end-to-end path (it's a Tier 1 change). The closest one is `tests/test_retro.py -k experience`, plus a direct run of the rating parser against hand-edited cells.
- I did not run the whole suite. `build/round-1.gate.md` records `GATE: PASS` with exit 0.
- I did not check the many test-only nit fixes (the other 18 files) one by one. The gate covers them.

## Evidence
$ cat .sdlc/work/201-tests-and-robustness-nits/build/round-1.gate.md | head -8
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ git diff $(git merge-base HEAD main) -- scripts/retro.py
(two hunks: `_num` wrapping in `_experience_text`, and `rating in EXPERIENCE_LABELS` in `_last_experience`)
exit: 0

$ uv run --group dev pytest tests/test_retro.py -q -k "experience"
21 passed, 266 deselected in 74.74s
exit: 0

$ python3 (inline script: parse a hand-edited rating cell with `indicators.report_rows`, then apply the new check)
3 3 3
3.0 3.0 3
abc None None
7 7 None
2.5 2.5 None
— None None
exit: 0
