# 192-tests-pruning — entries

## [2026-11-20-18] [idea] Narrow retro's tests.drifted to a test's own code and skip exact goldens

Left undone by 192-tests-pruning, carried forward when it landed: Retro's `tests.drifted` takes a test's code to be every code file its last change touched, so a test edited beside `sdlc.py` or `retro.py` drifts for good (`test_metrics.py`, `test_function_heat.py`), and an exact golden (`close-output.json`, `land-fix.txt`, `land-record-cases.json`) is named though it can't drift silently. A narrower notion of a test's code (the files it loads, or a host's list of goldens) would make the list worth acting on.
See .sdlc/work/192-tests-pruning/notes.md in its commit.
Raised 2026-11-20.
