VERDICT: PASS

The change builds what the spec describes. `train --run` landed three changes in a scratch repo with stand-in agents, and each stop and cancel case in the spec behaved as described. I did not run the real loop against a live host repo.

## Notes
- `checks.md`: the change has none, so there was nothing to read or run.
- Gate: `build/round-1.gate.md` is green. I did not run the gate again.
- End-to-end path: I ran the new tests. They cover the spec's R1 to R16: the batch of three, a stop at a kept change, a refusal, a refused push, a stall, the gate-fault ejection, the second-run refusal, cancel, kill and resume, the stored fix, parallel reviewers, `resolve` with `--onto` or `--continue`, a clean worktree after a resolution, ejection causes and the shared driver.
- The land skill's description and Step 0 now describe the unattended loop. They say a rerun resumes past a stop and that `train --cancel` stops a running loop. `test_land_runs_the_train_unattended` passes.
- Not run: `claude plugin validate` and the rest of the suite, which the gate already covered.
- The `pytest` call exceeded the foreground timeout and was moved to the background by the harness. I waited for it to finish and did not start a second copy.

## Evidence
$ uv run --group dev pytest -q tests/test_train.py -k "train_run or second_train or killed or ejection or resolution or driver" tests/test_land.py::test_resolve_needs_onto_or_continue tests/test_land.py::test_resolve_onto_the_base_outside_a_train tests/test_skills.py::test_land_runs_the_train_unattended
19 passed, 26 deselected in 194.44s (0:03:14)
exit: 0

$ tail -8 .sdlc/work/147-landing-runs-unattended/build/round-1.gate.md
    ✔ Validation passed
exit: 0

$ git status --short
 M AGENTS.md … M tests/test_train.py; ?? tests/train_driver.py
exit: 0

$ grep -n "run\b\|--run\|cancel" plugins/factory/skills/land/SKILL.md | head -20
(lines 32, 58 and 62 describe `train --run` and `train --cancel`)
exit: 0

$ cat .sdlc/work/147-landing-runs-unattended/checks.md
cat: No such file or directory (no checks.md exists)
exit: 0
