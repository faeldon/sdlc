VERDICT: PASS

The spec names no end-to-end command beyond status, so I ran `status --all` and the module and hand-gate tests. I did not compare output byte for byte against the pre-change code. The gate record and the pin tests cover that instead.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- `status --all` runs and lists changes 162, 163 and 164 in their sections.
- `scripts/factory_records.py` imports only standard-library modules, with no import of `sdlc`. This meets the spec's "pure, nothing from `sdlc.py`" requirement.
- `tests/test_modules.py` and `tests/test_hand_gate.py`: 67 passed. These include the pin tests and the test that fails when core opens a factory run file outside the module.
- The gate record shows `GATE: PASS`, with 2964 passed and 28 skipped, ruff clean, and plugin validation passed.
- A grep for factory run files opened in `sdlc.py`, `closing.py` and `board.py` found no direct opens.

## Evidence
$ head -5 .sdlc/work/163-factory-records-reader/build/round-1.gate.md
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ grep -n "exit\|passed" .sdlc/work/163-factory-records-reader/build/round-1.gate.md | head
14:    All checks passed!
61:    2964 passed, 28 skipped in 125.48s (0:02:05)
exit: 0

$ uv run --group dev pytest tests/test_modules.py tests/test_hand_gate.py -q 2>&1 | tail -4
67 passed in 30.85s
exit: 0

$ uv run --quiet --script scripts/sdlc.py status --all 2>&1 | head -15
■ Building: 2
    162  T2 build ...
    163  T2 build      1d  factory-records-reader ...
■ Ready: 1
    164  T2 test ...
exit: 0

$ grep -n "^import\|^from\|sdlc" scripts/factory_records.py | head -20
30:from __future__ import annotations
32:import getpass
33:import json
34:import re
35:import tempfile
36:import time
37:from pathlib import Path
exit: 0

$ grep -n "decision.md\|land-step\|round-" scripts/sdlc.py scripts/closing.py scripts/board.py | grep -i "open\|read_text\|exists" | head
(no matches)
exit: 1
