VERDICT: PASS

The change does what the intent says. `ask` returns `rebuild` for a kept default that a reviewer or the approver raised, when no later builder report has a `- BUILT: D<n>` line for it. A kept default the builder raised still returns `ship`.

The diff adds `unbuilt_defaults()` and calls it from `cmd_ask()`. The decide skill's `rebuild` wording is updated. Autopilot's `hold_causes()` now holds a change with such a default, which covers the intent's second open question.

## Notes
- The new tests pass, including the case where a reviewer's default is confirmed with no later builder report (`rebuild`) and the case where the builder's own default is confirmed (`ship`). I ran only the 29 tests in `tests/test_factory_decisions.py` and `tests/test_autopilot.py` matching the `-k` filter below, not the whole suite.
- The gate record `land-1.gate.md` reads `GATE: PASS`, exit 0. It is for the build the landing round committed.
- I didn't drive `ask` against a real change folder. The tests build the ledger and builder reports and run the same code path.
- `checks.md` does not exist for this change, so there are no acceptance checks to read.

## Evidence
$ cat .sdlc/work/218-ask-reviewer-defaults/build/land-1.gate.md | tail -8
    ✔ Validation passed
exit: 0

$ head -12 .sdlc/work/218-ask-reviewer-defaults/build/land-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ git diff e7ae798fa67a87470b1e7c5cf210823f4fedb3d0...HEAD -- plugins/factory/scripts plugins/factory/skills/decide
(diff showing `unbuilt_defaults()`, the `cmd_ask()` change, `hold_causes()` and the decide skill's `rebuild` wording)
exit: 0

$ uv run --group dev pytest -q tests/test_factory_decisions.py tests/test_autopilot.py -k "rebuild or reviewer or built or default"
29 passed, 130 deselected in 5.60s
exit: 0
