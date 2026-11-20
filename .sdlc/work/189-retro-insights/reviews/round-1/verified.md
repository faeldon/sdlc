- KEPT: test: C1: tests/test_retro.py: R6's "a failed git step leaves the draft for a rerun" has no test. The code does it: `scripts/retro.py` removes the draft only after the commit succeeds, and a failed `add` or `commit` returns early. Only the success path is tested. A change that unlinked the draft before the commit would pass every test.

## Notes
I read `cmd_retro_commit` and the existing insights tests, and ran nothing. `retro-commit` calls `subprocess.run` for `add` and `commit` directly, not `sdlc._git`, so a `sdlc._git` stub won't make the commit fail. The builder needs a real failure instead, such as a failing `pre-commit` hook in the test repo. The rerun step then removes the hook and expects the commit, with the draft removed.
