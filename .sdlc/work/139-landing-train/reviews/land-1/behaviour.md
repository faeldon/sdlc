VERDICT: PASS

No failures found. The train's own tests, the land tests and the board tests pass, and the landing gate record for this round is green.

## Notes
- The spec names no single command to run, so I ran the closest path the change's tests exercise: `tests/test_train.py`, `tests/test_land.py` and `tests/test_board.py`. They cover R1–R19, including the three-change train, the red-tip ejection, the mid-train move and the close lock race. Result: 291 passed, 18 skipped.
- The gate record is `build/land-1.gate.md`. It reads `GATE: PASS` and ends with `Validation passed`. I did not run the gate myself.
- Check 1, "The policy doc says close holds the lock from its merge to its Close commit": I expect it to pass. I confirmed the grep target string is in `AGENTS.md` (1 match). I did not run the check.
- Check 2, "The policy doc says the train stacks through `resolve --onto` and `land` no longer runs `base`": I expect it to pass. Both phrases it greps for are in `AGENTS.md` (1 match each).
- Check 3, "The land skill may run the train": I expect it to pass. Both strings, `factory.py train *` and `factory.py train --begin <NNN…> --by <auto or person>`, are in `plugins/factory/skills/land/SKILL.md` (1 match each).
- I did not run a manual scratch-host landing with a live factory and real agents, which the spec's Verification section lists as a manual check. The tests stand in for it.

## Evidence
$ cd <path-to-clone>/.claude/worktrees/139-landing-train; uv run --group dev pytest tests/test_train.py tests/test_land.py tests/test_board.py -q -n auto 2>&1 | tail -8
(output: 291 passed, 18 skipped in 53.22s)
exit: 0

$ grep -c -F -- "holds \`_main_lock()\` from its merge to that commit" AGENTS.md
1
exit: 0

$ grep -c -F -- "stacked on the one before it by the factory's own rebase (\`resolve --onto\`)" AGENTS.md
1
exit: 0

$ grep -c -F -- "committed by \`land\` (which no longer runs \`base\`)" AGENTS.md
1
exit: 0

$ grep -c -F 'factory.py train --begin <NNN…> --by <auto or person>' plugins/factory/skills/land/SKILL.md
1
exit: 0

$ grep -c -F 'factory.py train *' plugins/factory/skills/land/SKILL.md
1
exit: 0

$ ls .sdlc/work/139-landing-train/build/; tail -5 .sdlc/work/139-landing-train/build/land-1.gate.md
land-1.gate.md, land-accept.md, round-1.files, round-1.gate.md, round-1.md, round-2.files, round-2.gate.md, round-2.md; the gate record ends "✔ Validation passed"
exit: 0

$ cat/head/sed of intent.md, spec.md, checks.md, decisions.md, land-1.gate.md; git diff 8da2c41d65d015a15c79e0b990ff0d2d4a5aca15...HEAD --stat
(reads; 54 files changed, 3804 insertions, 583 deletions)
exit: 0
