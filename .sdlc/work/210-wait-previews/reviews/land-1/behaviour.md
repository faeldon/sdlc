VERDICT: PASS

The end-to-end path works, and I expect both checks in `checks.md` to pass.

## Notes
- **End-to-end path:** `sdlc.py preflight 210 --preview` prints the changed paths from the diff and ends with `… 26 more lines, shown above`. That is the cut line R3 names for a preview with no file yet. It exited 0. The only status changes after it are factory run records already in the tree, none from this command.
- **Tests I ran:** `tests/test_skills.py` and `tests/test_modules.py` selected with `-k "wait or preview"`: 73 passed.
- **The gate:** `build/round-1.gate.md` and `build/land-1.gate.md` both record PASS (`./check.sh`, exit 0).
- **Check "No WAIT's literal question changed (R11)":** I expect it to pass. I read the check and did not run it. A parallel diff of `skills` and `plugins/factory/skills` against the merge base, filtered for edited quoted question lines (`> \``), came back empty, exit 0.
- **Check "The docs say the yes options carry the draft as their preview (R13)":** I expect it to pass. I read the check and did not run it. A grep for the same sentences in `AGENTS.md`, `docs/CONTRIBUTING.md` and `docs/REFERENCE.md` found each of them.
- **Not run:** I did not run the full suite or the gate, as instructed. I did not run each skill's WAIT dialog end to end, because that needs an interactive session.

## Evidence
$ uv run --quiet --script scripts/sdlc.py preflight 210 --preview 2>&1 | tail -25
(tail) … 26 more lines, shown above
exit: 0

$ git status --porcelain | head
 M .sdlc/work/210-wait-previews/build/land-accept.md
 M .sdlc/work/210-wait-previews/runs/land-step.md
 M .sdlc/work/210-wait-previews/runs/land-times.jsonl
 M .sdlc/work/210-wait-previews/runs/reviewer-behaviour.sessions
?? .sdlc/work/210-wait-previews/build/land-1.gate.md
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py tests/test_modules.py -k "wait or preview"
73 passed, 435 deselected in 0.30s
exit: 0

$ sh -c '! git diff "$(git merge-base HEAD main)" -- skills plugins/factory/skills | grep -E "^[-+]> \`"'
exit: 0

$ grep -q "preflight NNN --preview" docs/REFERENCE.md
exit: 0

$ grep -q "writes as their \`preview\` (cut past 40 lines to its approving part" AGENTS.md
exit: 0

$ cat .sdlc/work/210-wait-previews/build/land-1.gate.md
GATE: PASS … Verdict: PASS, Command: ./check.sh, Exit: 0
exit: 0
