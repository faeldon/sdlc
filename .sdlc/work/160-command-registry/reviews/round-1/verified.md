- KEPT: test: C1: tests/test_registry.py:23: `HELPERS` omits `Command`, so no test compares the two copies of the class. `test_the_registry_copies_match` only checks the names in `HELPERS`. The two classes are identical today, so adding `"Command"` passes.

## Notes
I read `tests/test_registry.py` and the `Command` class in both scripts (`sdlc.py` lines 83–89, `factory.py` lines 127–133), and diffed the two copies. I ran no tests.
