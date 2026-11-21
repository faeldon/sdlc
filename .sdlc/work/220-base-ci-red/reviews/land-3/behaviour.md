VERDICT: PASS

The land-3 fix does what the person asked. The test passes and the gate record is green. No line in `SIGNAL_KINDS` exceeds 100 characters. `test_every_signal_has_a_kind` now stubs a red base CI, so the `ci` kind is reached.

## Notes
- `checks.md` was not run. I did not re-read its sections, because this round only wrapped a tuple and extended a test stub.
- The gate record `build/land-3.gate.md` ends with `Validation passed`. I read it and did not rerun the gate.
- I did not run the end-to-end path, because the spec names none for this fix. The nearest is the one named test.

## Evidence

$ cat .sdlc/work/220-base-ci-red/build/land-3.md | head -60; cat .sdlc/work/220-base-ci-red/build/round-*.gate.md | tail -5; ls .sdlc/work/220-base-ci-red/build
the builder's report (the `$ sed` and `awk` line-length checks, `pytest` and `ruff` runs it lists), the tail of `round-1.gate.md` ending `✔ Validation passed`, and the build folder listing including `land-3.gate.md`
exit: 0

$ git diff 2d0cd292bb5eeebed9ad5c79b141cdda9695e03e...HEAD -- tests/test_autopilot.py plugins/factory/scripts/landing.py
`SIGNAL_KINDS` wrapped over three lines with `"ci"` after `"issue"`; `land_signals` adds the `ci` signal when `pre["ci"]["state"] == "red"`; the test's `pre` gains a red `ci` entry
exit: 0

$ cat .sdlc/work/220-base-ci-red/build/land-3.gate.md | tail -15
...
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py::test_every_signal_has_a_kind
1 passed in 0.17s
exit: 0
