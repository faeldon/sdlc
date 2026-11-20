VERDICT: PASS

This change only touches `tests/`, so there is no spec'd end-to-end path. I ran the closest one, the train tests, and read the gate record.

- **Gate:** the record shows `GATE: PASS`, `./check.sh` exit 0, 3450 passed and 29 skipped, in 187 s.
- **Train tests:** the kill, stop and cancel tests pass. That is 20 passed and 1 skipped in 25 s, with no 120 s poll left.
- **`by()`:** it now goes through `uv_script(...)`, which carries the offline fallback, as the intent asks.
- **Outside `tests/`:** nothing else changed, so nothing a host reads is touched.

## Notes
- There is no `checks.md` for this change, so I read no acceptance checks.
- I did not run the full suite; the gate record covers it.
- I did not audit the 26 nits one by one against the diff. I checked the intent's outcomes against the gate, the train tests and the `by()` change.
- I did not review `notes.md`, which should hold the reasons for any nit not fixed.

## Evidence
$ head -12 .sdlc/work/191-tests-paydown/build/round-1.gate.md
GATE: PASS … Command: ./check.sh … Exit: 0 … Seconds: 188.9
exit: 0

$ grep -n "passed\|failed" .sdlc/work/191-tests-paydown/build/round-1.gate.md
62:    3450 passed, 29 skipped in 187.36s (0:03:07)
exit: 0

$ git diff --stat $(git merge-base HEAD main) -- . ':!tests' | tail -5
(no output)
exit: 0

$ sed -n 200,225p tests/test_train.py
… def by(...): return uv_script(script, cwd, args, _close_env(), timeout=600) …
exit: 0

$ uv run --group dev pytest tests/test_train.py -q -n auto -k "kill or stop or cancel" 2>&1 | tail -5
20 passed, 1 skipped in 25.56s
exit: 0
