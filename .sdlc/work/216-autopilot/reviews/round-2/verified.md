- KEPT: security: C1: plugins/factory/scripts/factory.py:3499: `_run_check()` passes no `env=`, so the host's check runs with `AUTOPILOT_RUN_ENV` set when the loop starts `gate`. `_sdlc()` strips only `UNSET_FOR_SDLC`, so `accept` does the same. `landing._run_env()` builds on `os.environ`, so a train's tip gate inherits it too. That is code the change wrote, running as a child of the loop.

## Notes
- I read `_claude()`, `agent_env()`, `_run_check()`, `_sdlc()`, `UNSET_FOR_SDLC` and `landing._run_env()`.
- `_claude()` already passes `env=agent_env()`. That is the finding round 1 kept, so C1 is not a repeat of it. It covers only the direct agent session, not the host's check or the `accept` commands.
- Only C1 is numbered in this round. The other items after "Settled:" are earlier rounds' changes, not new ones. I read them as settled and didn't answer them. They included a `status --json` claim: `sdlc.py status` has no `--json` option in `scripts/sdlc.py`, and `autopilot.py:289` still calls it. That is not a C-line this round, so I did not rule on it, but a builder should check it.
- I ran no tests.
