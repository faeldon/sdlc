VERDICT: PASS

The change does what its Approach says. The approver prompt, the decide skill, the README and REFERENCE all carry the new look wording. The two new tests and the two existing look tests pass, and the round-2 gate record is green. The intent describes no command to run, so I read the diff and ran the tests that pin the wording.

## Notes
- `checks.md` does not exist for this change, so there were no acceptance checks to read.
- `- ESCALATED: look: <what to look at> — <why>` still matches `REASON_RE` in `factory.py`. The regex takes everything after the colon as the reason, so the ` — ` separator needs no parser change, as the intent's constraints require.
- `look` and `gate` are still the only kinds. The decide skill's WAIT and its answers (`seen` / `checked something`) are unchanged.
- The approver still escalates a Critical or High finding still open, a disagreement, a departure from the spec, a requirement with no test, a destructive operation and a secret, whatever the spec says. A published interface is covered only by the person's approval, never by a default the approver settled or assumed.
- I did not run the whole suite. The gate record shows it green.

## Evidence
$ cat .sdlc/work/182-looks-name-their-target/build/round-2.gate.md | head -20
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
Tree: unchanged
exit: 0

$ git diff abf3852c6362da3bd0c03362a7b08cf1262a2c0f...HEAD -- plugins docs tests
(the diff of approver.md, decide/SKILL.md, plugins/factory/README.md, docs/REFERENCE.md and tests/test_skills.py)
exit: 0 (the same command line also ran `ls checks.md`, which exited 1: the file does not exist)

$ uv run --group dev pytest tests/test_skills.py -q -k "approver_raises_a_look or decide_names_what or every_reason_a_line or decide_asks_each_look"
4 passed, 415 deselected in 0.05s
exit: 0

$ grep -n "REASON_RE" plugins/factory/scripts/factory.py | head -3
384:REASON_RE = re.compile(r"^\s*- ESCALATED:\s*([^\s:]+):\s*(.+?)\s*$")
1875:        m = REASON_RE.match(line)
exit: 0
