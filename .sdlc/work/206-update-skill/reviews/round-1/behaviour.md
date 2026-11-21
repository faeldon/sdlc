VERDICT: PASS

The change does what the spec says, and I found nothing to change. I ran the one end-to-end path I could run here, `update` in this repo, which reads the plugin in place from a clone. I did not run the detection against a real release, which needs a plugin installed from a marketplace and the network. The offline detection test covers that case. The 47 `update` tests pass.

## Notes
- **checks.md, "AGENTS.md maps the hook and its cache (R10)":** I expect it to pass. AGENTS.md has the `**Updates: ...**` paragraph, and `grep -c 'sdlc-update.json' AGENTS.md` gives 1. `hooks/hooks.json` and the "That cache is the one write" phrase are in the same paragraph, which I did not read in full.
- **checks.md, "README's skill table lists /sdlc:update (R15)":** I expect it to pass. README line 29 starts with `| \`/sdlc:update\` |`.
- **R5 and R8 end to end:** `update` in this worktree returned `in_place: true`, empty `steps` and `installs`, a reason, and exit 0. `update --hook` printed nothing and exited 0. `status` ran and showed no update line.
- **Gate:** `build/round-1.gate.md` records `GATE: PASS` for `./check.sh`, exit 0.
- **Decisions D1–D5:** these are the builder's open defaults. None conflicts with the spec, so I raise no DECISION.
- **Not run:** the real-install steps (the `claude plugin` commands, with the network) and the full suite. The gate record covers the suite.

## Evidence
$ cat .sdlc/work/206-update-skill/build/round-1.gate.md | head -12
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
exit: 0

$ uv run --quiet --script scripts/sdlc.py update
{"running": "1.11.0", "latest": null, "in_place": true, "installs": [], "elsewhere": [], "restart_first": null, "steps": [], "reason": "the plugin is read in place from a clone: its version is whatever the checkout holds", ...}
exit: 0

$ uv run --quiet --script scripts/sdlc.py update --hook
exit: 0

$ uv run --quiet --script scripts/sdlc.py status | head -20
(status sections shown; no update line)
exit: 0

$ uv run --group dev pytest -q -k "update"
47 passed, 3642 deselected in 32.65s
exit: 0

$ grep -n '^| `/sdlc:update`' README.md; grep -c 'sdlc-update.json' AGENTS.md; ls hooks skills/update
29:| `/sdlc:update` | when a session says a release is out: this repo's update steps, run behind one yes |
1
hooks.json
SKILL.md
exit: 0
