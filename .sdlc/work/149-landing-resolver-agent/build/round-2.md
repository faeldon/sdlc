## Builder report: 149, round 2 (rework)

I made round 1's one kept change. The gate is green: 2838 passed, 28 skipped. Nothing is committed, and `HEAD` is still `7128522`.

### Kept changes
- **ux, `scripts/board.py:843`:** the card's `next:` line now reads "its agent is resolving a conflict: wait for it, or /sdlc-factory:land NNN if its session ended". I chose the neutral "its agent" over "its resolver": the card can't tell the train's resolver from the builder's single-change `resolve` task, which is still the builder's (spec, *Alternatives rejected*). The same wording now appears in `tests/test_board.py:1216` and `:1424` and in `docs/REFERENCE.md`'s board paragraph. Test first: I updated the two board tests' expected text, and 16 cases failed on the old string. After the change all 265 pass.

### plan.md
Its `scripts/board.py` line now names the card's `next:` string, the board tests and REFERENCE.md.

### Left over
None. There is still no `notes.md`. No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py   (expected text updated, board.py not yet)
16 failed, 249 passed, 28 skipped in 40.58s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py
265 passed, 28 skipped in 40.90s
exit: 0

$ grep -rn "builder is resolving" scripts docs tests plugins README.md
exit: 1

$ ./check.sh
293 files already formatted
2838 passed, 28 skipped in 113.82s (0:01:53)
✔ Validation passed
exit: 0

$ git log --oneline -1
7128522 Close 147-landing-runs-unattended
