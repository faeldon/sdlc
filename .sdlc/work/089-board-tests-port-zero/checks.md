# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The board's tests pick no port before binding it

Only putting `_free_port()` back, the window this change closed, could fail it.

```sh
! grep -q "_free_port" tests/test_board.py && grep -q "board.serve(repo, 0)" tests/test_board.py
```
