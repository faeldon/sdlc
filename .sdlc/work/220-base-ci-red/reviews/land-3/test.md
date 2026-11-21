VERDICT: PASS

The landing-3 fix does what the person asked, and I found nothing that needs changing.

- **`SIGNAL_KINDS`**: it now wraps over three lines. The `awk 'length>100'` check on `plugins/factory/scripts/landing.py` printed no line. `"ci"` sits after `"issue"`, which is where `land_signals()` adds the CI signal, so the order matches what the comment above the tuple says.
- **`test_every_signal_has_a_kind`**: the stubbed `pre` now carries `"ci": {"state": "red", ...}`. The test asserts `set(kinds) == set(SIGNAL_KINDS) - {"unread"}`, so it fails if `ci` is never produced. The builder's evidence shows it failing before the fix and passing after.
- **Gate**: `build/land-3.gate.md` reads `GATE: PASS` from `./check.sh`, and plugin validation passed in the tail I read. I did not run the whole suite or the gate.

## Notes

- Each `R<n>` the diff touches (the CI signal in `land_signals`, the red-base landing tests) has a test that fails without it. The builder ran the `red_base` and `unknown_base` tests in `tests/test_land.py` and they passed. I didn't run any test myself.
- `checks.md`: I did not read it this round and ran nothing from it.
- I read the rest of the diff only far enough to see the tracker's `ci()` and `base_ci()`. Earlier rounds already passed them, and this round's rework didn't touch them.
