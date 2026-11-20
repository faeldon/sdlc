VERDICT: PASS

The change does what the intent says, and I found nothing to send back.

- The gate record for round 1 is `GATE: PASS` with exit 0.
- I ran `tests/test_indicators.py` and `tests/test_retro.py` again, as they cover the narrowed `tests.drifted`, and all 375 passed.
- The diff narrows `drifted_tests` to the code a test loads, as the intent asks:
  - A data file such as a golden, fixture or prompt never drifts.
  - A change of more than 50 files still counts as a test's last change.
  - `retro` still only reads. It added a read-only `git show` reader.
- `notes.md` says what each of the drifted tests became.
- `docs/REFERENCE.md` now describes the new rule.
- The slow-test outcome ("under half of 231 s") is not shown in any evidence I have. I did not time the suite, because the whole-suite result is the gate's. The change folder holds no timing figures, and I did not run the merged train tests to measure them, so the claim is unchecked.

## Notes

- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- The spec names no end-to-end path beyond `retro`'s `tests.drifted` output. The closest one is what `tests/test_indicators.py` and `tests/test_retro.py` exercise, which I ran.
- I did not run `retro` against a live host history.
- `notes.md` leaves out an uncovered readiness refusal in `cmd_train` and the train's roughly 1,500 git calls. They are filed as left-out work and are not failures of this change.

## Evidence

$ head -8 .sdlc/work/200-tests-pruned-again/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: 5c842a17f4565e88
Exit: 0
exit: 0

$ uv run --group dev pytest tests/test_indicators.py tests/test_retro.py -q -n auto
375 passed in 74.44s (0:01:14)
exit: 0

$ git diff --stat
8 files changed, 338 insertions(+), 199 deletions(-)
exit: 0

$ git diff scripts/retro.py scripts/indicators.py docs/REFERENCE.md
(narrowed `drifted_tests`: `loads()`, `DATA_SUFFIXES`, `_reader()`, REFERENCE.md updated)
exit: 0
