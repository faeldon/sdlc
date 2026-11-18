VERDICT: PASS

## Notes
- **End-to-end path:** I compared the base's copy of both scripts (from `f13f6dcd`, unpacked into a scratch dir) with this change's copy.
  - **What I compared:** top-level `--help` and `--help` for all 73 commands across both scripts, plus the usage errors: `nosuch`, `ship`, `new x --tier 3`, `resolve --continue --abort`, `cases compare`, `preflight 001 --nits`, `factory.py` with no command, `factory.py start 1` and `factory.py land 001`.
  - **Result:** byte-identical output and exit codes, with one exception, which is an artifact of the comparison.
  - **The exception:** bare `sdlc.py` (the default `status`) printed an extra "Setup: set up with 1.9.0, the plugin is 1.10.0" nudge from the change's copy. The base copy was unpacked without `.claude-plugin/`, so it couldn't see the plugin version. The change doesn't cause it.
- **Gate:** `build/round-2.gate.md` and `build/land-1.gate.md` both end in "Validation passed". The last gate record is green.
- **Modules not in the diff:** `git diff f13f6dcd --name-only` for `closing.py`, `retro.py`, `board.py` and `landing.py` printed nothing, so R8 holds.
- **New tests:** `tests/test_registry.py` and `tests/test_modules.py` passed, 29 tests.
- **checks.md, read only (not run):**
  - *Help and usage errors match the base:* I expect it to pass. My equivalent comparison matched everywhere except the setup-nudge artifact. The check sets `SDLC_OWN_SCRIPT=off` and runs the base copy from a scratch dir that, like mine, has no plugin manifest. So bare `sdlc.py` isn't in its list, and its `run-cases` and `land-fix` lines are ones I didn't run, but they follow the same pattern.
  - *The loaded modules are not in the diff:* I expect it to pass, since the diff touches none of the four.

## Evidence
$ cat .sdlc/work/160-command-registry/build/round-2.gate.md | tail -8
    ✔ Validation passed
exit: 0

$ cat .sdlc/work/160-command-registry/build/land-1.gate.md | tail -8
    ✔ Validation passed
exit: 0

$ git diff f13f6dcd12f65da2c679dcfb881c6350c60b268a --name-only -- scripts/closing.py scripts/retro.py scripts/board.py plugins/factory/scripts/landing.py
(no output)
exit: 0

$ (scratch comparison of the base and the change: `--help` for both scripts and all 73 commands, plus the usage-error cases)
DIFF scripts/sdlc.py  (bare run only: extra "Setup: set up with 1.9.0, the plugin is 1.10.0" line, from the base archive lacking `.claude-plugin/`)
cmds=73 bad=1
exit: 0

$ uv run --group dev pytest tests/test_registry.py tests/test_modules.py -q
29 passed in 1.96s
exit: 0
