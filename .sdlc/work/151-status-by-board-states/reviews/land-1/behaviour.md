VERDICT: PASS

The change's `status` output matches the spec. I ran `sdlc.py status` against the rebased tree, and it prints the board's six states in the board's order. Empty states print a heading with a count of 0, and Landing lists 149 and 151 with `/sdlc:close`. The one conflict, in `scripts/board.py`, was in docstring text only, and the merge kept both edits. I did not rerun the gate, which `build/land-1.gate.md` records as PASS.

## Notes
- `checks.md` does not exist for this change, so there were no acceptance checks to read.
- I did not exercise the board server, because `status` was the end-to-end path.
- I did not see a "Needs you" section in this run, since nothing needed the person. The spec gives that section a heading of its own and keeps it first. I ran no tree where something needs the person.

## Evidence
$ ls .sdlc/work/151-status-by-board-states .sdlc/work/151-status-by-board-states/build; git diff 209db728ea4d982de879081404c7dfa01488e522...HEAD --stat
exit: 0

$ cat build/land-1.md; head -40 build/land-1.gate.md
(land-1.md says the one conflict was in `scripts/board.py` and was resolved; land-1.gate.md shows `Verdict: PASS`, `Exit: 0`)
exit: 0

$ uv run --quiet --script scripts/sdlc.py status | head -50
(the output shows ■ Planned: 3, Designing: 0, Building: 0, Ready: 0, Landing: 2 (149, 151 → /sdlc:close), then Unreleased: 42)
exit: 0

$ ls .sdlc/work/151-status-by-board-states/checks.md
ls: .sdlc/work/151-status-by-board-states/checks.md: No such file or directory
exit: 1
