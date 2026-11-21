Both requested changes are in place, and the diff shows nothing else wrong.

VERDICT: PASS

## Notes
- The `SIGNAL_KINDS` tuple is wrapped over three lines (`plugins/factory/scripts/landing.py:542-546`), and none is over 100 characters. `"ci"` now sits after `"issue"`, matching where `land_signals()` adds the CI signal, as the comment above the tuple promises.
- The `ci` signal is also covered in `land_signals()` and its docstring.
- `test_every_signal_has_a_kind` (`tests/test_autopilot.py`) now stubs a red base CI in `pre`. The test's "every kind reached" assertion can only pass if the `ci` kind is produced, so it fails without the signal.
- I read the gate record (`build/land-3.gate.md`) and the builder's evidence in `build/land-3.md`: the gate is green, and the builder reports the test failing before the fix and passing after.
- I ran no tests myself.
