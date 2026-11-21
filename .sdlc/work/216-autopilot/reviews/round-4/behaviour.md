VERDICT: PASS

The fixes for the three open findings are in the code, and the autopilot test file passes. I found no failures in the end-to-end path.

- **Agent sessions:** `_claude()` now passes `env=agent_env()` (factory.py:4330). That strips `AUTOPILOT_RUN_ENV` and `TRAIN_RUN_ENV`, so a builder session can't pass `--by autopilot`.
- **Host check and `accept`:** `factory.py` removes both markers from its own environment as it starts (`take_markers()`, factory.py:6653) and puts them back only for a loop's own children (`loop_env()`). So `_run_check()` (the gate), `_sdlc()` (and the `accept` checks it runs), git and hooks no longer inherit the marker.
- **Candidates:** `sdlc.py status --json` now exists (sdlc.py:10831). It printed `{"next_up": {"items": [...` with `id`, `theme` and `group` per item, so autopilot has candidates to read.
- **Tests:** `tests/test_autopilot.py` has tests for each of these: the agent env, a real `run_step` with and without the marker, and candidates read from the real `status --json`. All 54 pass. The full-suite gate record is green (`GATE: PASS`, exit 0).

## Notes
- **`checks.md`, "autopilot.py is a sensitive path beside landing.py":** I expect it to pass. `.sdlc/config.toml` lists `"plugins/factory/scripts/autopilot.py",` under `sensitive`; I confirmed the entry but did not run the `grep` itself.
- **`checks.md`, "The autopilot skill exists with its one WAIT":** I expect it to pass. `SKILL.md` exists and the Step 2 WAIT heading matches exactly once.
- I did not run a real `autopilot --run` against a model. It spends paid calls, and the real subprocess path is covered by the new tests.

## Evidence
$ cat .sdlc/work/216-autopilot/build/round-4.gate.md | head -8
GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: a4067803e636f19f
Exit: 0
exit: 0

$ sed -n 4305,4325p plugins/factory/scripts/factory.py
def agent_env() -> dict[str, str]:
    markers = (AUTOPILOT_RUN_ENV, landing.TRAIN_RUN_ENV)
    return {k: v for k, v in os.environ.items() if k not in markers}
exit: 0

$ sed -n 3425,3475p plugins/factory/scripts/factory.py
take_markers() / loop_env() / autopilot_running() shown
exit: 0

$ uv run --group dev pytest tests/test_autopilot.py -q -n auto
......................................................                   [100%]
54 passed in 48.12s
exit: 0

$ uv run --quiet --script scripts/sdlc.py status --json
{"next_up": {"items": [{"rule": "nits", "label": "nits", "title": "[docs] 14 open, cost S", "id": null, "kind": "nit", "theme": "docs", ... "group": "ready"}, ...
exit: 0

$ grep -n "autopilot.py\|^sensitive" .sdlc/config.toml | head -3
30:sensitive = [
38:  "plugins/factory/scripts/autopilot.py",
exit: 0

$ test -f plugins/factory/skills/autopilot/SKILL.md && grep -c '^## Step 2 — WAIT for explicit approval$' plugins/factory/skills/autopilot/SKILL.md
1
exit: 0
