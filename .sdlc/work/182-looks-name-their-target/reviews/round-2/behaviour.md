VERDICT: PASS

## Notes
- The round-1 kept change is fixed. `docs/REFERENCE.md:543-545` now gives the look line as `- ESCALATED: look: <what to look at> — <why>`. It also says the decide question quotes the target before ` — `.
- The approver prompt (`approver.md:100`) and the decide skill (`SKILL.md:77-83`) match that wording.
- `checks.md` doesn't exist for this change, so there is nothing to read or run.
- The spec names no end-to-end command. The closest path the change's own tests exercise is the look-wording tests. The three tests matching `look` in `tests/test_skills.py` and `tests/test_prompts.py` passed.
- The round-2 gate is green: `GATE: PASS`, exit 0.

## Evidence
$ cd <path-to-clone>/.claude/worktrees/182-looks-name-their-target; head -8 .sdlc/work/182-looks-name-their-target/build/round-2.gate.md
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ sed -n 543,545p docs/REFERENCE.md
escalated for (`- ESCALATED: look: <what to look at> — <why>`, filed in the ledger as
`(approver round <R>, look)`, its decide question quoting the target before ` — `),
exit: 0

$ grep -n "look" plugins/factory/skills/decide/SKILL.md | head
77:- A `look` item (`kind: look`, the approver's reason in `question`, its `reply` `decision.md`): read
exit: 0

$ uv run --group dev pytest tests/test_skills.py tests/test_prompts.py -q -k "look"
3 passed, 474 deselected in 0.11s
exit: 0
