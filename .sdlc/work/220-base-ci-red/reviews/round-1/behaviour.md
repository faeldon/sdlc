VERDICT: PASS

The spec names no command a person would type. The closest end-to-end path is the change's own tests, which drive `status`, `preflight` and `land-check` against the `gh` fake. They pass, and the three docs checks should pass as well.

## Notes
- **Gate:** `build/round-1.gate.md` is `GATE: PASS` with `Exit: 0` for build `faf263b91a59e4a1`. I did not run the gate again.
- **Tests I ran:** `tests/test_base_ci.py` (31 passed), plus the CI-related tests in `tests/test_preflight.py` and `tests/test_land.py` (48 passed in total, selected with `-k "ci or base or red or unknown"`).
- **Check 1, `ci()` listed in CONTRIBUTING.md:** I expect a pass. I ran the check's `grep` pattern as a count and the line matches once.
- **Check 2, REFERENCE.md paragraph:** I expect a pass. Both patterns match once, the `**CI on the base branch.**` heading and the closing `nothing new is shown.` line.
- **Check 3, AGENTS.md names `CI_CACHE`:** I expect a pass. The new wording matches once, and the old "That cache is the one write made with" sentence is gone (0 matches).
- **Not run:** a live `gh` call. I did not reach GitHub, so the tracker is covered only through the fake.

## Evidence
$ cat .sdlc/work/220-base-ci-red/build/round-1.gate.md | head -8
GATE: PASS
## Attempt 1
Verdict: PASS
Command: ./check.sh
Build: faf263b91a59e4a1
Exit: 0
exit: 0

$ uv run --group dev pytest -q tests/test_base_ci.py tests/test_preflight.py::test_preflight_reports_ci_and_never_refuses_on_it tests/test_land.py -k "ci or base or red or unknown"
48 passed, 84 deselected in 82.86s (0:01:22)
exit: 0

$ uv run --group dev pytest -q tests/test_base_ci.py
31 passed in 9.20s
exit: 0

$ grep -c '<each check pattern>' docs/CONTRIBUTING.md docs/REFERENCE.md AGENTS.md
CONTRIBUTING.md: 1; REFERENCE.md: 1 and 1; AGENTS.md: 1, and 0 for the removed sentence
exit: 0

$ git status --short
 M AGENTS.md
 M docs/CONTRIBUTING.md
 M docs/REFERENCE.md
 M plugins/factory/scripts/landing.py
 M scripts/sdlc.py
 M scripts/trackers/github.py
 M tests/conftest.py
 M tests/test_land.py
 M tests/test_preflight.py
?? tests/test_base_ci.py
exit: 0
