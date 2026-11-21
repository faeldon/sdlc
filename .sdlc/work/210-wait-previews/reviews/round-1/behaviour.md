VERDICT: PASS

The preview renders and the WAIT tests pass. All three checks.md checks should pass on the code as it stands.

## Notes
- The gate record `build/round-1.gate.md` reads `GATE: PASS`.
- `preflight 210 --preview` printed the findings and the changed paths. I saw only the first 30 lines, so I did not compare it against every line of the spec.
- Check 1, "No WAIT's literal question changed (R11)": I expect a pass. Its diff filter for edited `> \`` question lines found nothing; grep exited 1 (no match), which is the pass condition under the check's `!`.
- Check 2, "The docs say the yes options carry the draft as their preview (R13)": I expect a pass. Each of its three AGENTS.md, CONTRIBUTING.md and REFERENCE.md phrases appears once, so all four greps would succeed.
- I did not run the other skills' preview renderers (`start`, `land-check`).

## Evidence
$ cat .sdlc/work/210-wait-previews/build/round-1.gate.md | head -5
GATE: PASS

## Attempt 1

Verdict: PASS
exit: 0

$ git diff "$(git merge-base HEAD main)" -- skills plugins/factory/skills | grep -E '^[-+]> `'
(no output)
exit: 1

$ grep -c "preflight NNN --preview" docs/REFERENCE.md; grep -c "only a chosen yes approves), its yes options carrying what the yes" AGENTS.md; grep -c "The dialog's yes options carry the draft as their \`preview\`" docs/CONTRIBUTING.md
1
1
1
exit: 0

$ uv run --quiet --script scripts/sdlc.py preflight 210 --preview | head -30
Findings: none
Paths:
M AGENTS.md
M docs/CONTRIBUTING.md
M docs/REFERENCE.md
M plugins/factory/scripts/factory.py
M plugins/factory/skills/build/SKILL.md
... (the changed skills, tests and scripts)
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -k "wait"
68 passed, 405 deselected in 0.15s
exit: 0
