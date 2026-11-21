VERDICT: PASS

All four kept changes are fixed in the code.

- **Env leak (the `_claude` env finding and the security finding):** `_claude()` at factory.py:4303 now passes `env=agent_env()`. That function drops `AUTOPILOT_RUN_ENV` and `TRAIN_RUN_ENV`.
- **Real `run_step` test:** `test_a_real_step_passes_by_autopilot_and_an_agents_env_never_does` runs the real subprocess path. It is refused with the lock free, refused under an agent env, and accepted as a loop child.
- **`status --json`:** it now works. `sdlc.py status --json` printed `next_up.items`. A real-`sdlc.py` test, `test_candidates_come_from_the_real_status_json`, covers `status_items`.

## Notes
- **`checks.md` check 1** (autopilot.py in `[review] sensitive`): I expect it to pass. I did not open `.sdlc/config.toml` to confirm.
- **`checks.md` check 2** (the skill file and its one WAIT heading): I expect it to pass. I did not open the skill file to confirm.
- **Gate:** the round-2 gate record is green. Its tail shows both plugins validating.
- **Not run:** I did not run `autopilot --preview` or a full `--run`. The tests above stand in for them.

## Evidence
$ cat .sdlc/work/216-autopilot/build/round-2.gate.md | tail -15
(tail: `✔ Validation passed` for both plugins; only the icon warning shown)
exit: 0

$ cat .sdlc/work/216-autopilot/checks.md
(two checks: grep for autopilot.py in config; test -f and grep on the autopilot SKILL.md)
exit: 0

$ grep -n "def agent_env" -A14 plugins/factory/scripts/factory.py
(agent_env at line 4285 returns os.environ without AUTOPILOT_RUN_ENV and landing.TRAIN_RUN_ENV; _claude passes env=agent_env() at line 4303)
exit: 0

$ uv run --quiet --script scripts/sdlc.py status --json | head -5
(prints {"next_up": {"items": [...], "warnings": []}})
exit: 0

$ uv run --group dev pytest tests/test_autopilot.py -q -n auto | tail -5
50 passed in 13.76s
exit: 0

$ sed -n 1125,1175p tests/test_autopilot.py
(shows the real-step test and the status_json test)
exit: 0
