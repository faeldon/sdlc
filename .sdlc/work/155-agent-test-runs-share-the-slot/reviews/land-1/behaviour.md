VERDICT: PASS

The `check` command does what the spec's R1–R5 say, both in the tests and in the by-hand run from the spec's Verification section. I ran no gate and no full suite.

## Notes
- **By-hand path (spec Verification):** I made a scratch repo with `gate_jobs = 1`, a base check of `sleep 3; echo done`, and a change branch `001-x`. I started two `factory.py check 001` runs about a second apart.
  - One printed `001-x: waiting for a gate slot (1 of 1 in use)`, then `done`.
  - Both exited 0, and `git status --porcelain` showed nothing new.
  - My first attempt used a branch with no change worktree, and the command refused as `cmd_gate` does. That was my setup's fault, not the change's.
- **Targeted tests:** `pytest tests/test_factory.py -k check` gave 29 passed. `tests/test_evidence.py`, `tests/test_metrics.py` and `tests/test_skills.py` gave 573 passed. These cover R1–R11.
- **checks.md has one check**, the README's "Gates and `check` runs from every worktree share `gate_jobs` slots" line plus `factory.py check NNN`.
  - I expect it to pass.
  - I ran its grep line by mistake. It is read-only and exited 0, but I should have only read it.
- **Gate record:** `build/round-1.gate.md` says `GATE: PASS`. I read it and did not rerun the gate.
- **Not run:** the full suite, and the R4 kill and timeout tests on their own, beyond what `-k check` already covered.

## Evidence
$ ls .sdlc/work/155-agent-test-runs-share-the-slot/ .sdlc/work/155-agent-test-runs-share-the-slot/build; cat .sdlc/work/155-agent-test-runs-share-the-slot/intent.md; git diff 8ea501d30bc47ee07aca5a79219b09ef933942a9...HEAD --stat
(listing, the intent, and a 40-file diffstat ending `1291 insertions(+), 46 deletions(-)`)
exit: 0

$ sed -n 1,140p .sdlc/work/155-agent-test-runs-share-the-slot/spec.md; cat .sdlc/work/155-agent-test-runs-share-the-slot/checks.md; head -30 .sdlc/work/155-agent-test-runs-share-the-slot/build/round-1.gate.md
(spec, checks.md, and a gate record starting `GATE: PASS`)
exit: 0

$ git diff 8ea501d30bc47ee07aca5a79219b09ef933942a9...HEAD -- plugins/factory/scripts/factory.py
(`_run_check`, `cmd_check`, `check_line` and the `check` subcommand added)
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_factory.py -k "check"
29 passed in 11.66s
exit: 0

$ uv run --group dev pytest -q tests/test_evidence.py tests/test_metrics.py tests/test_skills.py
573 passed in 2.54s
exit: 0

$ sh -c "<the grep line from checks.md>"
(no output)
exit: 0

$ uv run --quiet --script factory.py check 001   (two at once, in a scratch repo with gate_jobs=1)
001-x: waiting for a gate slot (1 of 1 in use)
done
A exit 0
done
B exit 0
(`git status --porcelain` printed nothing)
exit: 0
