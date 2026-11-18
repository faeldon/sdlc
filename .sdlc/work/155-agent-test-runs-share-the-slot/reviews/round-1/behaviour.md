VERDICT: PASS

The background run of `factory.py check 155` finished. It ran the base branch's full check in the worktree, ended on "Validation passed" and exited 0, so `check` passes the command's exit code straight through. That settles the run I couldn't finish earlier. It also released its gate slot when it ended.

## Notes
- `checks.md`, "The factory's README says check runs share the gate slots": I expect it to pass. The README has the "Gates and `check` runs from every worktree share `gate_jobs` slots" line and `factory.py check NNN`. I did not run the check itself.
- The `check` tests in `tests/test_factory.py` pass (29). `tests/test_evidence.py`, `tests/test_metrics.py` and `tests/test_skills.py` also pass (573).
- No bare `./check.sh` remains in `plugins/factory/agents/*.md`.
- The refusal wording for an id with no worktree (`check 999`) differs from the spec's three refusal cases. It still prints `{"refusals": [...]}` and exits 1 without running anything.

## Evidence
$ uv run --group dev pytest -q -n 4 tests/test_factory.py -k "check"
29 passed in 32.32s
exit: 0

$ uv run --group dev pytest -q tests/test_evidence.py tests/test_metrics.py tests/test_skills.py
573 passed in 23.59s
exit: 0

$ tr '\n' ' ' < plugins/factory/README.md | tr -s ' ' | grep -c 'Gates and `check` runs from every worktree share `gate_jobs` slots'
1
exit: 0

$ grep -c 'factory.py check NNN' plugins/factory/README.md
1
exit: 0

$ grep -n "\./check.sh" plugins/factory/agents/*.md
exit: 1

$ uv run --quiet --script plugins/factory/scripts/factory.py check 999
{"refusals": ["run it from change 999's own worktree, or from the main checkout once /sdlc:intent has made one: this checkout is on '155-agent-test-runs-share-the-slot', and no worktree has that change's NNN-slug branch"]}
exit: 1

$ uv run --quiet --script plugins/factory/scripts/factory.py check 155 2>&1 | tail -3
✔ Validation passed
exit: 0
