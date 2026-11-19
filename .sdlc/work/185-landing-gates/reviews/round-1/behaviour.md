VERDICT: PASS

The named tests for the spec's rules pass, and the one acceptance check's expectation holds against the code as it stands.

## Notes
- **End-to-end path:** the spec names no command a person runs, so I ran the closest one, the train and land tests (a train of one running the build, unchanged checks run as stacked, a red build stopping the train, the read-only list, the approver's answer deciding a changed check). 84 passed.
- **checks.md, "The docs state the landing's new gates":** I expect it to pass. I read its greps rather than running the block. I ran the same five greps by hand, and the old wording is absent and the four new names are present.
- **Gate record:** `build/round-1.gate.md` is `GATE: PASS` (`./check.sh`, exit 0, tree unchanged). I did not rerun the full gate.
- **Decisions D1–D3:** these are the builder's own defaults, still unticked in `decisions.md`. I raised none of them again.

## Evidence
$ head -12 .sdlc/work/185-landing-gates/build/round-1.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Build: f0fa6f39539bd8ed
Exit: 0
Seconds: 162.4
Tree: unchanged
exit: 0

$ ! grep -rnI "The loop runs neither\.\|harness asks before every run" AGENTS.md plugins/factory
(no output)
exit: 0

$ grep -q "\`\[commands\] build\` for \`gate --land --build\`" AGENTS.md
exit: 0

$ grep -q "checks_clearance()" AGENTS.md
exit: 0

$ grep -q "land-checks" plugins/factory/skills/land/SKILL.md
exit: 0

$ grep -q "gate --land --build" plugins/factory/README.md
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_train.py tests/test_land.py -k "checks or build or read_only or approvers or already or taken or figures or land_question or recheck" 2>&1 | tail -8
84 passed in 109.20s (0:01:49)
exit: 0
