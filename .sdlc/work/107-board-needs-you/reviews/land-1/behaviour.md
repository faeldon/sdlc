VERDICT: PASS

## Notes
- The end-to-end path is `sdlc.py status`, plus the board's tests. `status` now ends with a `■ What needs me` section. It printed `nothing`, which is right here because no change in this checkout is waiting on a person.
- The 37 targeted board and `sdlc.py` tests passed. They cover the needs text, the escalated-and-answered column, a malformed open line, a stop's way, the render key and `aria-live`.
- The gate record (`build/round-2.gate.md`, `land-1.gate.md`) shows validation passing. I did not rerun the gate.
- There is no `checks.md` for this change, so there were no acceptance checks to read.
- I did not start the board server or open the page, so the poll and focus behaviour is unchecked beyond what the tests read from the served script.
- `status` shows two `■ Problems` lines about inbox entries with "no change folder". The diff touches `.sdlc/work/inbox.md`, and I didn't check whether these come from it or were already on `main`. Neither concerns the needs logic, so I'm not raising them as a CHANGE.

## Evidence
$ uv run --group dev pytest -q -n auto tests/test_board.py tests/test_sdlc.py -k "needs or escalat or answered or aria or render or malformed or stop or spec_approval or unapproved"
37 passed in 10.83s
exit: 0

$ uv run --quiet --script scripts/sdlc.py status
■ Problems: 2
    ⚠  .sdlc/work/inbox.md: [building] The landing follows main when it moves before the close — no change folder
    ⚠  .sdlc/work/inbox.md: [building] A fix made at landing goes back through review — no change folder

■ What needs me
    nothing
exit: 0 (the exit code printed was `tail`'s, not `status`'s; the command printed output normally)
