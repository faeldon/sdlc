- KEPT: code: C1: plugins/factory/scripts/factory.py:4431: `land-checks` crashes on a removed `checks.md`. `checks_clearance()` still returns step `checks` when `sha` is None, because `record is None or sha is None` sets it. `_land_task` (lines 4260-4267) only refuses when the step isn't `checks`, so it goes on to build the prompt. `landing.checks_sha(folder)` returns None for a missing file, so `None[:16]` raises `TypeError` at line 4431.

## Notes
I only read code: `factory.py` lines 4255-4285 and 4405-4445, and `landing.py`'s `checks_clearance` and `checks_sha`. I ran no tests and did not reproduce the crash.

I did not check what `_checks_now`/`_preflight` return when `checks.md` is missing. If it returned a `problem`, `checks_clearance()` would return step `accept` and the refusal would already hold, so a trace through `_preflight` would settle this.
