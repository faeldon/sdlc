VERDICT: PASS

The end-to-end path behaves as the spec says. `preflight` on this change gives all three passes `applies: false`, because a factory run has a `decision.md` (R2–R4, R19). The branches it names are `factory.md`, `recover.md` and `cases.md`, none of the three new ones, and `problems` is empty.

## Notes
- `checks.md` does not exist for this change, so there are no acceptance checks to read.
- The gate record `build/land-4.gate.md` is green. I did not rerun it.
- The selected preflight, findings, hand-gate and skills tests pass: 93 passed. They cover the per-pass conditions, the note lines, the evidence section and the `SKILL.md` line budget.
- I could not run the new passes end to end here. This is a factory run, so they are off by design. Only their tests exercise them.

## Evidence
$ uv run --quiet --script scripts/sdlc.py preflight 143 | tail -30
(tail shown: `passes` has security, behaviour and ui each `applies: false`, why "a factory run: its own reviewers ran"; `branches` is `factory.md`, `recover.md`, `cases.md`; `problems` is `[]`)
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_preflight.py tests/test_findings.py tests/test_hand_gate.py tests/test_skills.py -k "pass or ship or ui_complete or evidence or budget" | tail -5
93 passed in 6.98s
exit: 0

$ cat .sdlc/work/143-ship-review-parity/checks.md
`checks.md` does not exist: "No such file or directory".
exit: 1

$ ls .sdlc/work/143-ship-review-parity; tail -15 .sdlc/work/143-ship-review-parity/build/land-4.gate.md
The folder holds no `checks.md`. The tail of the gate record shows "✔ Validation passed" for both plugins.
exit: 0
