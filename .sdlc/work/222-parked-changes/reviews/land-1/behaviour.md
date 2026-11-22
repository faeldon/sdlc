VERDICT: PASS

The change's tests pass and all three checks in `checks.md` should pass. I did not run the park path against a real busy resource, and I did not run `factory.py` at all. The factory README, REFERENCE.md and AGENTS.md each describe the park as the spec says.

## Notes
- The gate record `build/land-1.gate.md` is 90 lines and ends in `✔ Validation passed`. I did not rerun the gate.
- `tests/test_factory_park.py` is the change's own test file, and all 22 tests in it passed. That file is the closest the repo has to an end-to-end run of the park.
- **README check:** I expect it to pass. `plugins/factory/README.md` has `[park]` at line 480, `# exit = 75 ` at 482, `deadline = 60 ` at 484, `retry = 5 ` at 486, and `EX_TEMPFAIL` at 483.
- **REFERENCE.md check:** I expect it to pass. The `### A host resource the check waits on…` heading is at line 220, and the three `SDLC-BUSY-` lines are at 238–240.
- **AGENTS.md check:** I expect it to pass. Both phrases are at lines 340–341.

## Evidence
$ cd <path-to-clone>/.claude/worktrees/222-parked-changes; ls .sdlc/work/222-parked-changes .sdlc/work/222-parked-changes/build; cat .sdlc/work/222-parked-changes/build/round-*.gate.md | tail -15; cat .sdlc/work/222-parked-changes/checks.md; git diff --stat 772f89c7216cdf10fac1b2fb9c615eb3fa63051a...HEAD | tail -20
(listing, gate tail ending `✔ Validation passed`, the three checks, and `67 files changed, 3057 insertions(+), 104 deletions(-)`)
exit: 0

$ grep -n "reads no state file but\|runs/parked.md\`, and the clock" AGENTS.md; grep -c . .sdlc/work/222-parked-changes/build/land-1.gate.md; tail -3 .sdlc/work/222-parked-changes/build/land-1.gate.md|cut -c1-100; grep -n "exit:" .sdlc/work/222-parked-changes/build/land-1.gate.md|head -3; uv run --group dev pytest tests/test_factory_park.py -q -n 0 2>&1 | tail -4; grep -n '^\[park\]\|^# exit = 75 \|^deadline = 60 \|^retry = 5 \|EX_TEMPFAIL' plugins/factory/README.md | head; grep -n '^### A host resource\|^SDLC-BUSY-' docs/REFERENCE.md
```
340:`verdicts` decides from the rounds alone and reads no state file but `runs/mended` and the vouched
341:`runs/parked.md`, and the clock only for a park ...
90
    ✔ Validation passed
22 passed in 19.69s
480:[park] ... 482:# exit = 75 ... 483: EX_TEMPFAIL ... 484:deadline = 60 ... 486:retry = 5
220:### A host resource the check waits on: the factory's `[park]`
238:SDLC-BUSY-RESOURCE: ... 239:SDLC-BUSY-HOLDER: ... 240:SDLC-BUSY-UNTIL: ...
```
exit: 0
