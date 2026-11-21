VERDICT: PASS

The change does what the spec says. The gate record is green, and the behaviour tests I ran pass. I ran no scratch-repo walk of the hook with a stale record. The only hook run was in this clone, where the plugin is read in place and prints nothing, as R8 requires.

## Notes
- No `checks.md` exists for this change, so there is nothing to read or run there.
- Read `setup_nudge()` against R1–R5:
  - A current record returns None before drift runs.
  - A stale record with clean drift returns None.
  - A stale record with pending drift returns the version line.
  - A drift that raises `OSError` or `ValueError` keeps the line.
- Ran 101 selected tests in `tests/test_setup_lifecycle.py`, `tests/test_update.py` and `tests/test_skills.py` (`-k "nudge or hook or drift or setup or reference or in_place"`). All passed.
- Decision D1 (the hook runs drift's local reads while the record is behind) is the builder's default and is not answered. I raise no blocking decision on it.

## Evidence
$ head -8 .sdlc/work/213-setup-nudge/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ uv run --group dev pytest -q tests/test_setup_lifecycle.py tests/test_update.py tests/test_skills.py -k "nudge or hook or drift or setup or reference or in_place"
101 passed, 436 deselected in 37.72s
exit: 0

$ git status --short
M AGENTS.md, docs/FEATURES.md, docs/REFERENCE.md, hooks/hooks.json, scripts/sdlc.py, skills/intent/SKILL.md, skills/status/SKILL.md, tests/test_setup_lifecycle.py, tests/test_skills.py, tests/test_update.py
exit: 0

$ grep -n "def setup_nudge" -A45 scripts/sdlc.py
(setup_nudge() as the spec's steps 1–5 describe)
exit: 0

$ uv run --quiet --script scripts/sdlc.py update --hook
(no output: the plugin is read in place in this clone, so the hook prints nothing)
exit: 0
