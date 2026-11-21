VERDICT: PASS

I ran the autopilot path as far as it can run without a paid model call. It works as the spec describes.

## Notes
- **End-to-end path:** `factory.py autopilot` accepts the spec's commands: `--preview`, `--begin`, `--run`, `--cancel` and `--summary`, with `--seeds`, `--themes`, `--usd`, `--hours` and `--level`. The 54 tests in `tests/test_autopilot.py` pass. I did not start a real run, since that would spend model calls and write real state.
- **The gate:** its record for this round, `build/land-1.gate.md`, shows 3947 passed, 29 skipped, and the plugin validation passed. I did not rerun the whole suite.
- **Check 1, `autopilot.py` is a sensitive path:** I expect it to pass. `.sdlc/config.toml` line 38 lists `"plugins/factory/scripts/autopilot.py",` with the trailing comma the grep needs.
- **Check 2, the autopilot skill has its one WAIT:** I expect it to pass. `skills/autopilot/SKILL.md` line 95 is `## Step 2 — WAIT for explicit approval`, and the file exists.

## Evidence
$ cat .sdlc/work/216-autopilot/build/land-1.gate.md | grep -n -E "passed|failed|exit|error"
    3947 passed, 29 skipped in 256.87s (0:04:16)
    ✔ Validation passed
    ✔ Validation passed
exit: 0

$ grep -n 'autopilot.py' .sdlc/config.toml
38:  "plugins/factory/scripts/autopilot.py",
exit: 0

$ grep -n '^## Step 2' plugins/factory/skills/autopilot/SKILL.md
95:## Step 2 — WAIT for explicit approval
exit: 0

$ uv run --group dev pytest tests/test_autopilot.py -q -n auto
54 passed in 59.14s
exit: 0

$ tail -5 .sdlc/work/216-autopilot/build/land-1.gate.md
    ✔ Validation passed
exit: 0

$ uv run --quiet --script plugins/factory/scripts/factory.py autopilot --help
usage: factory.py autopilot [-h] (--preview | --begin | --run | --cancel | --summary) [--seeds ID [ID ...]] [--themes THEME [THEME ...]] [--usd USD] [--hours HOURS] [--level {1,2}]
exit: 0
