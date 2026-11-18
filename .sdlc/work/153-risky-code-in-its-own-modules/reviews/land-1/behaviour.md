VERDICT: PASS

## Notes
- The spec's end-to-end path passes. The moved functions are gone from `sdlc.py` and `factory.py`. The `--help` output of 6 `sdlc.py` commands and 6 `factory.py` commands is identical to the base's. `factory.py verdicts 153` reports `"depth": "full"` with `closing.py` and `landing.py` as the sensitive paths. `tests/test_modules.py` passes, 13 tests.
- `.sdlc/config.toml` lists both new modules under `[review] sensitive`.
- The gate records `round-1.gate.md` and `land-1.gate.md` both read `GATE: PASS`. I did not rerun the gate.
- There is no `checks.md` for this change, so there are no acceptance checks to read.
- I did not run `git diff <base> -- tests/` to check that no expected value was edited, because the gate is green. I did not run the Windows subset or the change's own close handoff.

## Evidence
$ git grep -nE '^def (cmd_close|_main_lock|_push|_push_plan|_lock_depth)\b' scripts/sdlc.py
(no output)
exit: 1

$ git grep -nE '^def (cmd_land|cmd_train|cmd_resolve|_run_loop)\b' plugins/factory/scripts/factory.py
(no output)
exit: 1

$ diff of `sdlc.py` `--help`, `close --help`, `publish --help`, `release --help`, `new --help` and `inbox-commit --help`, base against HEAD
sdlc --help diff exit: 0
sdlc close --help diff exit: 0
sdlc publish --help diff exit: 0
sdlc release --help diff exit: 0
sdlc new --help diff exit: 0
sdlc inbox-commit --help diff exit: 0
exit: 0

$ diff of `factory.py` `--help`, `land --help`, `land-check --help`, `train --help`, `resolve --help` and `land-verdicts --help`, base against HEAD
factory --help diff exit: 0
factory land --help diff exit: 0
factory land-check --help diff exit: 0
factory train --help diff exit: 0
factory resolve --help diff exit: 0
factory land-verdicts --help diff exit: 0
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py verdicts 153 | grep -E 'depth|sensitive'
  "depth": "full",
  "sensitive": [
  "why": "the diff touches sensitive path(s) plugins/factory/scripts/landing.py, scripts/closing.py",
exit: 0

$ uv run --group dev pytest tests/test_modules.py -q
13 passed in 1.16s
exit: 0

$ head -12 .sdlc/work/153-risky-code-in-its-own-modules/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0

$ head -8 .sdlc/work/153-risky-code-in-its-own-modules/build/land-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0

$ grep -n -A8 sensitive .sdlc/config.toml
36:  "scripts/closing.py"
37:  "plugins/factory/scripts/landing.py"

$ ls .sdlc/work/153-risky-code-in-its-own-modules/checks.md
ls: No such file or directory
exit: 1
