VERDICT: PASS

The kept change was made. `test_a_failed_commit_leaves_the_insights_draft_for_a_rerun` in `tests/test_retro.py` installs a pre-commit hook that exits 1. It then checks that `cmd_retro_commit` returns 1 with a `git commit failed` refusal, that the draft is still on disk, and that HEAD is unchanged. After the hook is removed, the rerun commits and removes the draft and writes the report with the Insights section. It passed when I ran it alone. The gate record for round 2 reads PASS.

I did not run an end-to-end retro; the new test covers that path. The test fails the commit with a real git hook, not a `sdlc._git` stub, which is a stronger test than the one the kept change asked for.

## Notes
- `checks.md`: not present in the change folder, so there is nothing to read.
- Not run: the whole suite, per the gate-record rule.

## Evidence
$ cat .sdlc/work/189-retro-insights/build/round-*.gate.md | tail -15
(both records, GATE: PASS; the lines shown are validation output ending `✔ Validation passed`)

$ head -12 .sdlc/work/189-retro-insights/build/round-2.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0

$ sed -n 5055,5100p tests/test_retro.py
(the new test, as described above)

$ uv run --group dev pytest tests/test_retro.py::test_a_failed_commit_leaves_the_insights_draft_for_a_rerun -q
1 passed in 0.59s
exit: 0
