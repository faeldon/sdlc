VERDICT: PASS

The gate is green and the end-to-end test passes. The spec's outcomes are all covered by tests or stated in the docstrings.

## Notes
- There is no `checks.md` for this change, so there were no acceptance checks to read.
- The end-to-end path is `test_autopilot_run_lands_a_seed_through_real_subprocesses`. It ran as a real subprocess loop with a stand-in `claude`, and passed.
- The marker tests also passed: `take_markers`, the agent session never carrying the loop's markers, and the changes' own code never running as a loop child.
- The rest of the diff behaves as the spec says:
  - A refused agent now records `closes:` before it writes a session or a landing step (R6).
  - `unfenced_lines()` stops a `- BUILT:` line inside a code fence from counting as built (R8).
  - The docstrings on `cmd_answer`, `cmd_decisions` and `recorded_closes` now say why the missing lock is safe.
- I ran only the named tests (24 of them). I did not run the whole suite; I cite the gate record for that.

## Evidence
$ cat .sdlc/work/228-autopilot-readiness/build/round-1.gate.md | head -12
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: b308289f5999e973
Exit: 0
Seconds: 319.5
Waited: 1699.4
Tree: unchanged
exit: 0

$ ls .sdlc/work/228-autopilot-readiness .sdlc/work/228-autopilot-readiness/build; head -60 .sdlc/work/228-autopilot-readiness/intent.md; git diff 6e4ce0fad0db1e76af20c68fa1b01eadfe665b07...HEAD --stat | tail -20; cat .sdlc/work/228-autopilot-readiness/checks.md
(listing, intent and stat printed; checks.md: No such file or directory)
exit: 1

$ git diff 6e4ce0fad0db1e76af20c68fa1b01eadfe665b07...HEAD -- plugins/factory/scripts/factory.py plugins/factory/README.md; grep -n "^def test" tests/test_autopilot.py | tail -12
(diff and test list printed)
exit: 0

$ uv run --group dev pytest -q tests/test_autopilot.py tests/test_land.py tests/test_factory_decisions.py -k "real_subprocesses or take_markers or closes_once or ledger_writer or fence or markers or refused or built"
........................                                                 [100%]
24 passed, 249 deselected in 42.22s
exit: 0

$ timeout 500 uv run --group dev pytest -q tests/test_autopilot.py -k "..."
zsh: command not found: timeout
exit: 127
