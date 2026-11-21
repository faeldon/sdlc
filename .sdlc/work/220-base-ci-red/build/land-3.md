Both parts of the fix are made.

**What I changed**
- **`SIGNAL_KINDS`** (`plugins/factory/scripts/landing.py`): I wrapped the tuple over three lines, and none is over 100 characters now. Before, one line was 103: since my last round, `"ci"` had been moved to sit just before `"unread"`. I put it back after `"issue"`. That is where `land_signals()` adds the CI signal, and the comment above the tuple says the kinds follow that order.
- **`test_every_signal_has_a_kind`** (`tests/test_autopilot.py`): the stubbed `pre` now has a red base, `"ci": {"state": "red", "branch": "main", "sha": "abcdef1234567890", "url": "https://ci/1"}`. The `ci` kind is now produced, and the test's "every kind reached" check passes with it.

The test was failing before this fix, because no `ci` kind was ever produced. It now passes, as do all 57 autopilot tests and the two red-base and unknown-base landing tests. Ruff's lint and format checks pass on both files.

## Evidence

$ sed -n 538,547p plugins/factory/scripts/landing.py | awk '{print length": "$0}'
103:     "resolved", "fixed", "unreviewed", "auto_off", "undone", "checks", "cases", "nits", "ci", "unread",
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py::test_every_signal_has_a_kind
FAILED tests/test_autopilot.py::test_every_signal_has_a_kind - AssertionError...
1 failed in 10.77s
exit: 1

$ uv run --group dev pytest -q tests/test_autopilot.py::test_every_signal_has_a_kind tests/test_land.py -k "every_signal_has_a_kind or red_base or unknown_base"
3 passed, 99 deselected in 2.56s
exit: 0

$ awk 'NR>=541 && NR<=546 && length>100 {n++} END {print (n+0)" lines over 100"}' plugins/factory/scripts/landing.py
0 lines over 100
exit: 0

$ uv run --group dev ruff check plugins/factory/scripts/landing.py tests/test_autopilot.py
All checks passed!
exit: 0

$ uv run --group dev ruff format --check plugins/factory/scripts/landing.py tests/test_autopilot.py
2 files already formatted
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_autopilot.py
57 passed in 6.22s
exit: 0
