VERDICT: PASS

The recorded prompt copies match the old script's output, and the new prompt files, validation and tests all behave as the spec says. I ran only the named prompt tests, never the whole suite. The gate record is green.

## Notes
- **End-to-end path.** The spec has no CLI path of its own: the change is a pure move of the prompt text. The closest path is the golden test (R2/R3), which renders each task's prompt and compares it with `tests/prompts/*.txt`. I ran it two ways:
  - Against the new `factory.py`, all 59 tests in `tests/test_prompts.py` pass.
  - Against the base branch's `factory.py` and `landing.py`, taken from `git archive HEAD` into a scratch directory and passed through `SDLC_FACTORY_UNDER_TEST`, the 46 recorded-copy cases also pass. So the copies were recorded from the old script, not from the refactor (R3).
- **Files.** `plugins/factory/prompts/` holds 15 files: the 14 listed in the spec plus `common.md`.
- **R10.** `tests/test_factory.py` has a one-line diff, the rename of `factory.RECHECK` to `factory.prompt_part("spec", "recheck")`, which is the only kind of edit R10 allows.
- **`checks.md`.** There is none in this change folder, so there were no acceptance checks to read.
- **Not done.** I did not run `check.sh` or the full suite, because the gate record covers that.

## Evidence
$ head -20 .sdlc/work/164-prompts-in-files/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
(the record shows a green run)
exit: 0

$ ls plugins/factory/prompts tests/prompts
15 prompt files; 46 recorded copies
exit: 0

$ uv run --group dev pytest tests/test_prompts.py -q
59 passed in 2.39s
exit: 0

$ SDLC_FACTORY_UNDER_TEST=<scratch>/plugins/factory/scripts/factory.py uv run --group dev pytest tests/test_prompts.py -q -k recorded_copy
46 passed, 13 deselected in 21.17s
exit: 0

$ git diff --stat tests/test_factory.py
 tests/test_factory.py | 1 insertion(+), 1 deletion(-)
exit: 0
