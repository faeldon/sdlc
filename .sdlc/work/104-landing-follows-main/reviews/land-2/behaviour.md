VERDICT: PASS

The change is rebased onto `main` and `main` is an ancestor of `HEAD`. The tests I ran pass, and I found nothing that fails against the spec.

## Notes
- **`checks.md`:** the change has none, so there are no acceptance checks to read.
- **Gate record:** `build/land-2.gate.md` is `GATE: PASS` (`./check.sh`, exit 0) on build `96f0f6417a6f`. That is the commit now at `HEAD`, so the record covers this build. I didn't run the gate myself.
- **End-to-end path:** the spec's path is the landing following a moved `main`, then re-gating and re-reviewing, and `yes, with a fix`. `tests/test_land.py` exercises it, including a test that moves `main` between review and close. I ran it with the metrics and skills tests, and 499 tests passed.
- **Spec fields in code:** the `[land] moves` key (default 3) exists in `factory.py`. `land_question()` takes `moves` and words the follow clause and the fourth answer.
- **Stale spec text:** the builder's `land-1.md` notes that `spec.md` and `plan.md` still quote the landing question as it read before `main` moved. The question is now composed by `land_question()`. This is documentation drift only, not a CHANGE.
- **Not run:** I ran no live landing against a real moved `main`. Only the test fixtures cover that.

## Evidence
$ git merge-base --is-ancestor main HEAD
exit: 0

$ head -8 .sdlc/work/104-landing-follows-main/build/land-2.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Build: 96f0f6417a6f2bc7
Exit: 0

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_metrics.py tests/test_skills.py
499 passed in 20.57s
exit: 0
