The ux reviewer's one KEPT change is done, and the gate passes: 2252 passed, 13 skipped. The work is still uncommitted.

- **ux, `factory.py:1985`:** `WAYS_WHY["mend"]` no longer says "mends it once". It now reads "Rerunning /sdlc-factory:build {id} asks an agent again, once, for the reply in its shape; if that reply still lacks it, ship it by hand with /sdlc:ship {id}." I also added a check to `test_each_way_on_fits_two_lines_at_phone_width` that neither the `NEXT:` line nor the longer text says "mend" for any stop. That test failed before the rewording and passes now.

The word `mend` stays in a few places a person doesn't read: the `STOPPED:` value in `runs/stopped.md`, which the code parses, and the docstrings.

`plan.md` is unchanged, since the build still matches it, and nothing new went into `notes.md`. No new decisions this round.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k fits_two_lines   (red, before the rewording)
FAILED tests/test_factory.py::test_each_way_on_fits_two_lines_at_phone_width
1 failed, 210 deselected in 3.68s
exit: 1

(The shell printed `exit: 0` after the `tail` it was piped through. pytest itself exited 1, as the FAILED line shows.)

$ ./check.sh
All checks passed!
2252 passed, 13 skipped in 225.83s (0:03:45)
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py tests/test_board.py -k "fits_two_lines or says_why"
2 passed, 353 deselected in 39.57s
exit: 0
