I made the fix in `docs/REFERENCE.md`, and nothing else changed. I ran no git command.

1. **The `status` line paragraph (around line 657):** it now says a `mend` stop being mended reads `mending` with no `⚠` lines. Its `→` line is `the factory is mending the <role>: wait for it`. It stays off Needs you until the mend replies or runs past the agent's 3-hour timeout. "Being mended" means `agent --task mend` has recorded the mend in `runs/step.md`.
2. **The Needs-you list (around line 674):** it now includes the timed-out mend's text: `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it`.

I checked that both texts are what `scripts/sdlc.py` prints. The nine test files that read `docs/REFERENCE.md` pass: 1139 tests. My first try at that run collected nothing because zsh didn't split the file list, so I reran it with the files named one by one.

## Evidence

$ sed -n 652,682p docs/REFERENCE.md
…A `mend` stop its supervisor is mending (`agent --task mend` has recorded it in `runs/step.md`) reads `mending` instead, with no `⚠` lines and `→ the factory is mending the <role>: wait for it`, and stays off Needs you until the mend replies or runs past the agent's 3-hour timeout…
…`stopped: free what it waits on and rerun` for a park past its deadline, and `stopped: mending the <role> since HH:MM with no reply: rerun /sdlc-factory:build NNN if no session runs it` for a mend past the agent's timeout), `parked past its deadline: free <resource>`…
exit: 0

$ grep -n '"mending, "\|the factory is mending the\|elif rec.get("stopped")' scripts/sdlc.py
10985:            "mending, " if rec.get("mend_running")
11003:        lines.append(f"{indent}→ the factory is mending the {mend['role']}: wait for it")
11004:    elif rec.get("stopped"):
exit: 0

$ files=$(grep -l "REFERENCE.md" tests/*.py | tr '\n' ' '); uv run --group dev pytest -q -n 4 $files
no tests ran in 3.13s
exit: 4

$ uv run --group dev pytest -q -n 4 tests/test_defaults.py tests/test_findings.py tests/test_factory_docs.py tests/test_feature_map.py tests/test_nits.py tests/test_release.py tests/test_retro.py tests/test_skills.py tests/test_update.py
1139 passed in 77.88s (0:01:17)
exit: 0
