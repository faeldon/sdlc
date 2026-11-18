VERDICT: PASS

## Notes
- **End-to-end path:** I ran `.sdlc/function-heat.py` in the worktree. It prints a ranked table for each of the four files, 15 rows a file, ordered by commits then size. It exited 0 and cites the boundary commit `40b6888` (2026-11-18). That matches the Outcome.
- **`sdlc.py retro`:** I did not run it. It writes a report, and the `[retro] indicators` line is not on the base branch yet. The indicator command is wired in `.sdlc/config.toml` line 62 and runs correctly on its own.
- **Gate:** `round-1.gate.md` shows `GATE: PASS`, exit 0, from `./check.sh`.
- **Check 1, config line:** I expect it to pass. Line 62 is exactly `indicators = ["uv run --quiet --script .sdlc/function-heat.py"]`, which `grep -qx` matches.
- **Check 2, four-script table:** I expect it to pass. The output has the standalone lines `scripts/sdlc.py` and `plugins/factory/scripts/landing.py`.
- **Decisions D1–D3:** the builder's defaults are consistent with the intent's Outcome and Approach, so I raised nothing against them.

## Evidence
$ git status --short; grep -n -B3 -A3 indicators .sdlc/config.toml
```
 M .sdlc/config.toml
 M tests/test_windows.py
?? .sdlc/function-heat.py
?? .sdlc/work/161-function-heat/
?? tests/test_function_heat.py
62:indicators = ["uv run --quiet --script .sdlc/function-heat.py"]
```
exit: 0

$ uv run --quiet --script .sdlc/function-heat.py
```
Function hotspots: commits that rewrote some of each top-level function since the retrospective at 40b6888 (2026-11-18).

scripts/sdlc.py
  commits  lines  function
        2    476  main
        2    228  cmd_release
...
plugins/factory/scripts/landing.py
  commits  lines  function
        1    172  cmd_resolve
...
```
exit: 0

$ head -12 .sdlc/work/161-function-heat/build/round-1.gate.md
```
GATE: PASS
Command: ./check.sh
Exit: 0
```
exit: 0
