VERDICT: PASS

Round 1's kept change, C1, is fixed. `HELPERS` in `tests/test_registry.py` now includes `"Command"`, so the test compares both copies of the class.

## Notes
- **Spec path:** the move must leave `--help`, usage errors and exit codes identical to the base. I compared 8 invocations in a scratch dir, `--help`, an unknown command, `status --help` and `close --help` for each script, and none differ from the base's output.
- **Whole suite:** `build/round-2.gate.md` says `GATE: PASS` on its first attempt, with `./check.sh` exiting 0. I did not rerun it.
- **checks.md, "Help and usage errors match the base":** I did not run it, and expect it to pass. My subset matched, and the gate is green. The other checked invocations, such as `new x --tier 3` and `resolve --continue --abort`, go through the same registry parser.
- **checks.md, "The loaded modules are not in the diff":** I did not run it, and expect it to pass. My `git diff --name-only` over `closing.py`, `retro.py`, `board.py` and `landing.py` printed nothing.

## Evidence
$ grep -n "HELPERS" -A6 tests/test_registry.py | head -20
```
23:HELPERS = ("UsageError", "Command", "arg", "exclusive", "command", "_parser")
171:@pytest.mark.parametrize("name", HELPERS)
172:def test_the_registry_copies_match(name: str) -> None:
173:    """R12: `factory.py` never imports `sdlc.py`, so it keeps a copy of the registry, pinned."""
174:    assert _source(FACTORY_PY, name) == _source(SDLC_PY, name)
```
exit: 0

$ uv run --group dev pytest tests/test_registry.py -q -p no:xdist 2>&1 | tail -4
```
................                                                         [100%]
16 passed in 0.79s
```
exit: 0

$ git diff $(git merge-base HEAD main) --name-only -- scripts/closing.py scripts/retro.py scripts/board.py plugins/factory/scripts/landing.py
```
(no output)
```
exit: 0

$ SDLC_OWN_SCRIPT=off; git archive base | tar -x -C $t; for each script and each of `--help`, `nosuch`, `status --help`, `close --help`: run the base copy and the built copy, `cmp` their output plus exit code
```
bad=0
```
exit: 0

$ cat .sdlc/work/160-command-registry/build/round-2.gate.md | head -12
```
GATE: PASS
Verdict: PASS
Command: ./check.sh
Exit: 0
```
exit: 0
