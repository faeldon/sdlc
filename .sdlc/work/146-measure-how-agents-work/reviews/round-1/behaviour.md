VERDICT: PASS

The background run of my own has now finished. It passed all 459 tests in `tests/test_metrics.py`, `tests/test_retro.py` and `tests/test_archive.py`, so my earlier "not run" for those files no longer applies.

The earlier "Not run" note on `measure_change()` and retro against real transcripts still applies. Only fixture tests cover those.

## Notes
- **`checks.md`:** none exists for this change, so there are no acceptance checks to read.
- **End-to-end path:** the spec names no command a person runs, only `measure` at close, which writes `Sdlc-*` trailers that retro reads. The closest path I ran was `metrics._shell` on sample commands, plus the tests that exercise `measure_change()` and retro on fixtures.
  - **Counted:** `> out.txt` and `sed -i` as shell edits; an inline `python -c` with `open(..,'w')` as a shell edit; a trailing `&` as background; `pytest` and `./check.sh | tail` as test runs.
  - **Not counted:** `2>&1`, `> /dev/null`, a read-only `python -c`, `a && b`, `grep pytest x`.
- **Requirements:** R1–R15 are covered by named tests, and those passed in the gate and in my run. R16 (docs) is for the code review.

## Evidence
$ uv run --quiet python -I - (calls `metrics._shell` on 10 sample commands, then runs `pytest -q -n auto tests/test_metrics.py tests/test_retro.py tests/test_archive.py | tail -3`; run in the background, output read from its output file)
'echo hi > out.txt' (True, False, False)
'cmd 2>&1' (False, False, False)
'x > /dev/null' (False, False, False)
'sed -i s/a/b/ f' (True, False, False)
'python3 -c "open('f','w').write('x')"' (True, False, False)
"python -c 'print(1)'" (False, False, False)
'uv run --group dev pytest -q &' (False, True, True)
'a && b' (False, False, False)
'./check.sh 2>&1 | tail' (False, False, True)
'grep pytest x' (False, False, False)
459 passed in 197.35s (0:03:17)
exit: 0

$ cd .sdlc/work/146-measure-how-agents-work && ls -R . | head -50; cat intent.md; cat spec.md | head -150
(intent and spec read; they name no end-to-end command)
exit: 0

$ cat build/round-1.gate.md | tail -15; cat checks.md
(gate: validation passed; `checks.md` does not exist)
exit: 1

$ head -8 .sdlc/work/146-measure-how-agents-work/build/round-1.gate.md; cat .sdlc/work/146-measure-how-agents-work/build/round-1.md | head -60; git status --short | head -20
GATE: PASS
Attempt 1, Verdict: PASS, Command: ./check.sh, Exit: 0
All 16 requirements are built and the full gate passes (2623 passed, 18 skipped).
 M docs/REFERENCE.md
 M scripts/metrics.py
 M scripts/retro.py
 M scripts/sdlc.py
 M tests/test_archive.py
 M tests/test_metrics.py
 M tests/test_retro.py
exit: 1 (the trailing `ls` of the missing `checks.md`)

$ grep -n "^def \(read_events\|summarize\|trailers\|parse_trailers\|_run\|_behaviour\|_shell\)" scripts/metrics.py
451:def _behaviour …; 497:def _run …; 680:def _shell …; 789:def read_events …; 1014:def summarize …; 1522:def trailers …; 1618:def parse_trailers …
exit: 0

$ Read of the background task's output file
(the pytest line and the `_shell` lines above)
exit: 0
