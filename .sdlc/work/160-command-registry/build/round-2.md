I've fixed the one kept change: the R12 test now also pins the `Command` class, so the two scripts' copies of it can no longer drift apart unnoticed.

- **KEPT `tests/test_registry.py:25`, `Command` not pinned:** I added `"Command"` to `HELPERS`, which now reads `("UsageError", "Command", "arg", "exclusive", "command", "_parser")`. `COMMANDS` and `HELP_ORDER` stay out, since they differ per script. To confirm the test now catches a mismatch, I temporarily changed `Command.__init__` in `sdlc.py` only. `test_the_registry_copies_match[Command]` failed, and after I put the file back as built it passed. `sdlc.py` is byte-identical to the round-0 build (checked with `cmp`).

`tests/test_registry.py` now has 16 tests and all pass; ruff check and format are clean. `plan.md` already said `Command` is pinned by this test, and that is now true, so it is unchanged. Nothing new in `notes.md`. I didn't rerun the whole suite, since the gate runs it on this rework.

No decisions raised.

## Evidence

$ uv run --quiet --group dev pytest -q "tests/test_registry.py::test_the_registry_copies_match[Command]"   (sdlc.py's Command temporarily changed)
1 failed in 0.12s
exit: 1

$ uv run --quiet --group dev pytest -q tests/test_registry.py   (sdlc.py restored)
16 passed in 8.72s
exit: 0

$ uv run --quiet --group dev ruff check tests/test_registry.py && uv run --quiet --group dev ruff format --check tests/test_registry.py
All checks passed!
1 file already formatted
exit: 0

$ cmp scripts/sdlc.py /tmp/registry_build/sdlc.bak && echo restored
restored
exit: 0
