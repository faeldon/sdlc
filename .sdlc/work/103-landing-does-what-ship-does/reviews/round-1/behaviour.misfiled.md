VERDICT: PASS

The landing does what the spec says, and I found nothing to send back. I ran the change's own landing tests, which stand in for the end-to-end path.

R13's test runs a batch of three changes through `factory.py` alone: one with `checks.md`, one with an undone note, and one touching an irreversible path. The spec gives no other path. The skills' cases can't run in a scratch repo, so R5's test covers them with a stand-in.

## Notes
- `checks.md` does not exist for this change, so there is nothing to read or run.
- Every spec test I checked exists and passes. They cover R1, R2, R3, R4, R5, R7, R8, R10, R11 and R13. I did not run the R6 test, `test_no_skill_lets_accept_run_unasked`.
- R6: `land`'s `allowed-tools` grants no `factory.py accept` or `factory.py cases` rule. Step 3 names both commands, so the harness prompts before each run. I did not read `check.sh` or the CI files for the two commands, and the grep over `.github` returned nothing, so I read that as absent.
- R14: the skill description and README no longer say checks, cases and notes are shipped by hand. The remaining "by hand" mentions are about a change built by hand, or one with an irreversible path and no `- RECOVER:` line, which stays excluded as R10 says.
- The landing gate record, `build/land-1.gate.md`, reads `GATE: PASS`. I did not rerun the gate.

## Evidence
$ uv run --group dev pytest -q -n auto tests/test_land.py
26 passed in 6.93s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k "factory_alone or carries_drops or checks_or_undone or names_only or refuses_a_change or runs_its_checks or proposes_dispositions or accept_records or cases_writes or run_unasked"
9 passed, 17 deselected in 15.86s
exit: 0

$ grep -n "^def test_" tests/test_land.py | grep -E "factory_alone|carries_drops|in_the_batch|names_only|refuses_a_change|runs_its_checks|proposes_disp|accept_records|cases_writes|each_changes"
10 matching test definitions (lines 315–1013), covering R1–R5, R7, R8, R10, R11 and R13
exit: 0

$ grep -rn "factory.py. accept\|factory.py.* cases" plugins/factory/skills/*/SKILL.md check.sh .github
plugins/factory/skills/land/SKILL.md:110: the only match, in the Step 3 prose
exit: 0

$ sed -n 1,20p plugins/factory/skills/land/SKILL.md; grep -n "by hand" plugins/factory/skills/land/SKILL.md plugins/factory/README.md
allowed-tools lists config, sdlc-path, land-check, land, resolve, agent, gate and land-verdicts only; the "by hand" matches are the ones described in Notes
exit: 0

$ head -5 .sdlc/work/103-landing-does-what-ship-does/build/land-1.gate.md
GATE: PASS
exit: 0
