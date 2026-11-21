VERDICT: PASS

## Notes

**What this round changed.** The fix in `build/land-3.md` touches two places, and neither crosses a trust boundary:
- **`SIGNAL_KINDS`** (`plugins/factory/scripts/landing.py:542`): the tuple is wrapped over three lines, and `"ci"` is put back after `"issue"`, which is the order `land_signals()` adds signals in. The order has no security effect, because the tuple is only read as a set:
  - `autopilot.py:184-185` builds the risk-budget keys from it, so `ci` gets `RISK_OTHER` weight. A red base therefore adds to autopilot's risk and can't be dropped from it.
  - `tests/test_autopilot.py:228` and `:283-284` also use it as a set.
- **`test_every_signal_has_a_kind`** (`tests/test_autopilot.py:272`): the stubbed `pre` now includes a red `ci` reading, so the test reaches the `ci` kind. The data is only test data: a fake sha and the URL `https://ci/1`, with no secrets.

**The whole diff, checked again for this landing.** The diff runs from `2d0cd29` to `HEAD`. The code in `scripts/sdlc.py`, `scripts/trackers/github.py`, `landing.py` and `tests/conftest.py` matches what I passed in round 1:
- `gh` is called with an argv list and no shell, given a timeout, and only runs whose `headSha` matches the tip are kept.
- Any failure reads as `unknown`, never red, and core checks `state ∈ CI_STATES` before it uses a reading.
- The cache sits in the git common dir and is written through a temp file and `os.replace`.
- A red reading is added after preflight's problems are built, so it can't refuse a change.
- `land_signals()` builds the signal text with f-strings, and nothing runs that text.

The rework didn't touch any of this, and nothing new can be exploited.

**What I checked.**
- `git diff 2d0cd29...HEAD` (the stat, and the code paths in full).
- `build/land-3.md`, and the gate record `build/land-3.gate.md`, which is PASS (`./check.sh`, exit 0).
- The round-1 security review, and `decisions.md`: R1 and R2 are the person's fix, now made.
- A grep for where `SIGNAL_KINDS` is used, and an `awk` check that no line in either edited file is over 100 characters (none is).
