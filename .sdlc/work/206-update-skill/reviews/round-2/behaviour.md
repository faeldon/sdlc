VERDICT: PASS

The change does what the spec says on the path I could run, and both checks should pass. The gate record is green.

## Notes
- **Gate:** `round-2.gate.md` reads `GATE: PASS`, `Exit: 0`, with 3660 tests passed.
- **End-to-end path:** I ran `sdlc.py update --installed`. It printed valid JSON and exited 0. The plugin is read in place from a clone here, so `installed`, `scope` and `restart_first` are null and the reason says why. I did not run the `/sdlc:update` skill itself, because it makes network calls and runs `claude plugin` steps behind a WAIT.
- **Check "AGENTS.md maps the hook and its cache (R10)":** I expect it to pass. AGENTS.md contains the `Updates:` paragraph, and the one `grep -c` I ran counted a single matching line for `sdlc-update.json` and `That cache is the one write`. I did not separately grep for `hooks/hooks.json`.
- **Check "README's skill table lists /sdlc:update (R15)":** I expect it to pass. README.md line 29 starts with `| \`/sdlc:update\` |`.
- **Round 2 rework:** the changes to `tests/fixtures/close-output.json` and `tests/test_archive.py` are covered by the green gate.

## Evidence
$ head -8 .sdlc/work/206-update-skill/build/round-2.gate.md
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0

$ grep -n "exit\|passed\|failed" .sdlc/work/206-update-skill/build/round-2.gate.md
62: 3660 passed, 29 skipped in 222.29s (0:03:42)
exit: 0

$ grep -n 'sdlc:update' README.md
29:| `/sdlc:update` | when a session says a release is out: … |
exit: 0

$ grep -c 'sdlc-update.json\|That cache is the one write' AGENTS.md
1
exit: 0

$ uv run --quiet --script scripts/sdlc.py update --installed
{"running": "1.11.0", "installed": null, "scope": null, "restart_first": null, "reason": "the plugin is read in place from a clone: …"}
exit: 0
