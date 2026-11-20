VERDICT: PASS

The change did what its intent says, on the checks I ran. I did not run the retro command end to end. `retro` writes its report, so it isn't read-only. The new `tests.drifted` rule is checked only through `tests/test_retro.py` and `tests/test_indicators.py`, which pass.

## Notes
- **checks.md:** the change has none, so there is nothing to read.
- **Gate:** the record shows `GATE: PASS`.
- **Slow tests:** `notes.md` lists what became of each of the eight, and the merged tests still pass. The three it says it folded away were my only check on the "each still fails without the code it covers" outcome. I didn't repeat the mutation runs in the build report.
- **Drifted tests:** `notes.md` accounts for the nine, and for a twelfth the old rule also named. Only `tests/test_function_heat.py` still drifts, and it says why.
- **Left out:** `notes.md` files two follow-up seeds, one on the train's repeated git reads and one on a readiness refusal no test would catch.

## Evidence
$ cat .sdlc/work/200-tests-pruned-again/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ uv run --group dev pytest -q tests/test_indicators.py tests/test_retro.py tests/test_train.py tests/test_land.py -n auto
618 passed, 1 skipped in 131.87s (0:02:11)
exit: 0

$ git diff --stat b51bdcdd4b98b27305852122edad03671d65d35b...HEAD | tail -20
 26 files changed, 957 insertions(+), 199 deletions(-)
exit: 0

$ cat .sdlc/work/200-tests-pruned-again/notes.md | head -70
(the notes, as quoted above)
exit: 0
