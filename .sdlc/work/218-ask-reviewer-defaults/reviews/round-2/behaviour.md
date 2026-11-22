VERDICT: PASS

Round 2's rework works as the intent and the D2 answer describe. I ran only the named tests, not the suite.

## Notes
- **`checks.md`:** none exists. It is optional at Tier 1, so there is nothing to read or expect.
- **End-to-end path:** the intent names `ask --answered`. Its tests are the closest runnable path:
  - A reviewer's confirmed default with no later builder report gives `rebuild`.
  - The builder's own default still goes to `ship`.
  - A later `- BUILT: D<n>` line clears the reviewer's default.
- **Autopilot:** D2 was answered as "autopilot holds such a change". `hold_causes()` in `autopilot.py` now calls `factory.unbuilt_defaults()` and adds a hold reason for any unbuilt default. The `tests/test_autopilot.py` additions pass.
- **Gate:** round 2's record says `GATE: PASS`, with `./check.sh` at exit 0.

## Evidence
$ cat .sdlc/work/218-ask-reviewer-defaults/build/round-2.gate.md | head -15
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: 607b5279d1c527cc
Exit: 0
Seconds: 295.3
Waited: 0.0
Tree: unchanged
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py tests/test_autopilot.py -k "default or unbuilt or built or reviewer"
29 passed, 127 deselected in 6.78s
exit: 0

$ sed -n 560,600p plugins/factory/scripts/autopilot.py
(`hold_causes()` shown: calls `factory.unbuilt_defaults(folder, open_lines)` and appends "a reviewer's or the approver's default no build made: <ids>")
exit: 0

$ git diff --stat <merge-base>
9 files changed, 166 insertions(+), 16 deletions(-)
exit: 0

$ grep -n "unbuilt_defaults\|BUILT_RE" -r plugins tests
plugins/factory/scripts/factory.py:415:BUILT_RE = re.compile(...)
plugins/factory/scripts/factory.py:2295:def unbuilt_defaults(...)
plugins/factory/scripts/factory.py:2385:out["unbuilt"] = unbuilt_defaults(folder, kept)
exit: 0
