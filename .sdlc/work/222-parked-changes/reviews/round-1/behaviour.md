VERDICT: PASS

Checking the park path, I read the spec and the gate record, then ran the park-related tests. All of them passed, and every test the spec names exists. I didn't run the scratch-host path from the spec's Verification; the tests exercise the same behaviour.

## Notes
- `checks.md` doesn't exist for this change, so there are no acceptance checks to read.
- The spec's end-to-end path is a manual run in a scratch host: set `[park] exit = 75`, make the check print the `SDLC-BUSY-*` lines and exit 75, then watch the card, the `status` line and the stop. I did not run it. Instead I ran the tests that cover it: `-k "park or busy or slot or step_has_a_row or parked"` gave 46 passed.
- Those tests include the gate park, re-park, deadline and forged-record cases, the slot wait, the autopilot wait and the `STEPS` table.
- The round-1 gate record is `GATE: PASS` (`./check.sh`, exit 0). I did not rerun the gate.
- `decisions.md` has D1–D4. They are builder defaults, all unticked, and each is within what the spec says. I raised none of them again.

## Evidence
$ cat .sdlc/work/222-parked-changes/build/round-1.gate.md | head -12
GATE: PASS
## Attempt 1
Verdict: PASS
Command: ./check.sh
Build: f30460293b8498d1
Exit: 0
exit: 0

$ uv run --group dev pytest -q -n auto -k "park or busy or slot or step_has_a_row or parked" tests/
..............................................                           [100%]
46 passed in 17.44s
exit: 0

$ for t in <the 8 named tests>; do grep -rl "def $t" tests; done
test_factory_park.py (7 of the tests), test_autopilot.py (test_autopilot_waits_out_a_park_and_holds_past_its_deadline)
exit: 0

$ git status --short | head
 M AGENTS.md
 M docs/FEATURES.md
 M docs/REFERENCE.md
 M plugins/factory/README.md
 M plugins/factory/scripts/autopilot.py
 M plugins/factory/scripts/factory.py
 M plugins/factory/scripts/run_state.py
 M plugins/factory/skills/build/SKILL.md
 M scripts/board.html
 M scripts/board.py
exit: 0
