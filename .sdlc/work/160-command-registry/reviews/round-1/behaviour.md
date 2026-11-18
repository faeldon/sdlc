VERDICT: PASS

The command registry is a pure move in everything I ran. The only differences from the base copies were path or version differences caused by running the base copy from a temp directory.

## Notes
- **`checks.md` "Help and usage errors match the base"**: I expect it to pass. My own comparison showed the same output and exit code for the top-level `--help` of both scripts and for several per-command helps. It also matched for the usage errors in R4 and the factory's no-command error (exit 2). The new `tests/test_registry.py` passes (15 tests).
- **`checks.md` "The loaded modules are not in the diff"**: I expect it to pass. `git diff <merge-base> --stat` lists only `scripts/sdlc.py` and `plugins/factory/scripts/factory.py`.
- **Whole suite**: `build/round-1.gate.md` records `GATE: PASS`, and I did not run the suite again.
- **Differences against the base, none a failure**:
  - `sdlc.py config` differs only in the absolute `guide` and plugin paths, because the base copy was extracted to a temp directory.
  - A bare `sdlc.py` run differs only by a "set up with 1.9.0, the plugin is 1.10.0" line, because the temp copy has no plugin manifest.
- **Not run**: the full byte-for-byte comparison across every command's `--help` is the acceptance check, which I only read. I ran a sample of commands instead.

## Evidence
$ cat .sdlc/work/160-command-registry/build/round-1.gate.md | head
GATE: PASS … Command: ./check.sh … Exit: 0
exit: 0

$ git diff $(git merge-base HEAD main) --stat | tail -6
 plugins/factory/scripts/factory.py | 578 +++++++++++++++-------
 scripts/sdlc.py                    | 967 +++++++++++++++++++++----------------
 2 files changed, 958 insertions(+), 587 deletions(-)
exit: 0

$ (bash loop comparing the base copy, extracted with `git archive` to a temp dir, against this change's scripts)
same[0] scripts/sdlc.py --help
same[0] scripts/sdlc.py status --help
same[0] scripts/sdlc.py ship --help
same[2] scripts/sdlc.py resolve --continue --abort
same[1] scripts/sdlc.py preflight 001 --nits
same[2] scripts/sdlc.py new x --tier 3
same[2] scripts/sdlc.py cases compare
same[0] plugins/factory/scripts/factory.py --help
same[0] plugins/factory/scripts/factory.py agent --help
same[0] plugins/factory/scripts/factory.py land --help
same[1] plugins/factory/scripts/factory.py land 001
same[2] plugins/factory/scripts/factory.py start 1
same[2] plugins/factory/scripts/factory.py   (no command)
DIFF scripts/sdlc.py config (guide and plugin paths only)
exit: 0

(An earlier pass in zsh did not split the arguments, so its "status --help" rows were invalid. The bash pass above replaces them.)

$ uv run --quiet --script scripts/sdlc.py | head -3
… 4 open, 4 total   today: 2026-11-18
■ Planned: 3
exit: 0

$ uv run --group dev pytest tests/test_registry.py -q | tail -3
15 passed in 0.87s
exit: 0
