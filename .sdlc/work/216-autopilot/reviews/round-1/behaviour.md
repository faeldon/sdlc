VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/autopilot.py:289: `status_items()` runs `sdlc.py status --json`, but `sdlc.py status` takes only `--all`. Argparse rejects `--json`, so `autopilot --preview` prints the warning `sdlc.py status couldn't be read: … unrecognized arguments: --json` and `candidates` is always `[]`. A real `--run` would never find a seed and would stop at once. The spec's R10 assumes `status --json` exists, and no part of this change adds it. Either add a `--json` output with `next_up.items` (id, group, theme) to `sdlc.py status`, or read the candidates another way. The tests don't catch this, apparently because the call is stubbed.

## Notes
- checks.md, "autopilot.py is a sensitive path beside landing.py": I expect it to pass. `.sdlc/config.toml:38` holds `"plugins/factory/scripts/autopilot.py",`.
- checks.md, "The autopilot skill exists with its one WAIT": I expect it to pass. The skill file exists and line 93 is `## Step 2 — WAIT for explicit approval`.
- The gate record (`build/round-1.gate.md`) says `GATE: PASS`, exit 0.
- D1 and D2 in `decisions.md` are builder defaults that are still open. They are not raised again here.
- I did not run `autopilot --run` or `--begin`, because both start a paid, unattended run. I ran `--preview`, `--summary`, one refused `land --by autopilot` call, and the new test file.

## Evidence
$ cat .sdlc/work/216-autopilot/build/round-1.gate.md | head -20
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0

$ grep -n 'autopilot.py' .sdlc/config.toml
38:  "plugins/factory/scripts/autopilot.py",
exit: 0

$ grep -n '^## Step 2' plugins/factory/skills/autopilot/SKILL.md
93:## Step 2 — WAIT for explicit approval
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py autopilot --preview --usd 5 --hours 2 --level 1
… "candidates": [], … "shown": "…First candidates, in rank order:\n- none within the bounds…" … "warnings": ["sdlc.py status couldn't be read: … sdlc.py: error: unrecognized arguments: --json"] …
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py land 216 --by autopilot
"state": "refused", "refusals": ["--by autopilot is autopilot's alone: no autopilot --run holds its lock"]
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py autopilot --summary
{"refusals": ["no autopilot run to summarise"]}
exit: 0

$ uv run --group dev pytest tests/test_autopilot.py -q -n auto
47 passed in 17.56s
exit: 0

$ uv run --quiet --script scripts/sdlc.py status --help
usage: sdlc.py status [-h] [--all]
exit: 0

$ git grep -n '"--json"' -- scripts/sdlc.py
scripts/sdlc.py:3985: return [*argv, "--json", str(run / "result.json")]
scripts/sdlc.py:9580: ["claude", "plugin", "list", "--json"],
exit: 0
