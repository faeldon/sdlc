The gate record for this round is green, and I read the full diff against the spec. A named-test run I started timed out and went to the background. I'm finishing on the gate record, not on that run.

VERDICT: PASS

## Notes
- NIT: scripts/retro.py:377: `_is_process` also skips `.sdlc/setup.json` (`sdlc.MANIFEST`), which R3 doesn't list. The path is under `.sdlc/` anyway. The skip only stops a change that touched just `setup.json` from counting as process work. REFERENCE.md says so, but the spec doesn't. Drop the skip or add it to the spec. {docs S low}
- NIT: scripts/retro.py:~560: `_milestone_follow` can't see a milestone's seed that was retired with `inbox-commit`, so it reads `carried` where `_seed_follow` reads `dropped`. The builder filed this in `notes.md`. It is worth a seed. {robustness M med}
- NIT: scripts/metrics.py:746: the new `bg` regex counts an unquoted `&` inside a URL such as `curl x?a=1&b=2`. That is a real background `&` in shell, so this is correct, but a test case for it would pin the choice. {tests S low}

**Done well:**
- `value_band()` is the single function `retro()` and `retro_report()` both call, so the JSON and the report can't drift apart.
- `_followed` keeps unmeasured milestones out of `n`, so nothing reads as zero.
- `_register_at` is factored out of `_none_themes` instead of copied.
- Missing data is null with a stated reason throughout.

**Run:** none to completion. The gate record (`build/round-1.gate.md`) is `GATE: PASS`. The builder's focused run of `test_retro.py` and `test_metrics.py` also passed (354). I started a rerun of the new tests and it timed out into the background; I did not wait for it.
