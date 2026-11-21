VERDICT: PASS

## Notes
- The end-to-end path is `update --hook`, which printed nothing and exited 0. In this clone the running plugin is read in place, so the spec says it isn't checked or told. `update --installed` printed the expected in-place JSON, with `installed: null` and `restart_first: null`.
- Check "AGENTS.md maps the hook and its cache (R10)": I expect it to pass. I ran its four greps as plain reads, not through `accept`. All four matched, so the heading and the three strings are in `AGENTS.md`.
- Check "README's skill table lists /sdlc:update (R15)": I expect it to pass. The `grep` for the table row matched.
- The gate record for this landing round, `land-1.gate.md`, starts with `GATE: PASS`.
- I did not run the update check against the network or against an installed copy. That would need a non-in-place install, and a fake of `claude plugin list` is already covered by `tests/test_update.py`, which I did not rerun.

## Evidence
$ cd <path-to-clone>/.claude/worktrees/206-update-skill; ls .sdlc/work/206-update-skill .sdlc/work/206-update-skill/build; cat .sdlc/work/206-update-skill/build/round-*.gate.md | tail -15; git diff 6ef608ae14eb9f18feacd69186ac096bb70fcc65...HEAD --stat | tail -20
(the round gates ended in "✔ Validation passed"; the diff is 52 files, 2873 insertions and 16 deletions)
exit: 0

$ head -5 .sdlc/work/206-update-skill/build/land-1.gate.md
GATE: PASS
exit: 0

$ uv run --quiet --script scripts/sdlc.py update --hook
(no output)
exit: 0

$ uv run --quiet --script scripts/sdlc.py update --installed | head -20
{"running": "1.11.0", "installed": null, "scope": null, "restart_first": null, "reason": "the plugin is read in place from a clone: its version is whatever the checkout holds"}
exit: 0

$ grep -q '^\*\*Updates: `cmd_update()` and the one hook.\*\*' AGENTS.md && grep -q 'hooks/hooks.json' AGENTS.md && grep -q 'sdlc-update.json' AGENTS.md && grep -q 'That cache is the one write' AGENTS.md
exit: 0

$ grep -q '^| `/sdlc:update` |' README.md
exit: 0
