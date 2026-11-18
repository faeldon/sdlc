VERDICT: PASS

The end-to-end path matches the spec. Running `sdlc.py status` in this worktree prints the board's states in order: Planned, Designing, Building, Ready, Landing. After them come Unreleased, Next up, Release due and Problems, and `■ Needs you` is the last section. The old *Open changes*, *Shipped*, *Ready to close* and *What needs me* headings no longer appear. Empty states print their heading with a count of 0, as R6 says. The status and board tests pass.

I did not rerun the gate. I read `build/round-1.gate.md`, which ends in a passing validation.

## Notes
- `checks.md`: the change has none, so there was nothing to read or expect.
- Decisions D1 and D2 are the builder's own defaults, still unticked. D1 keeps *Needs you* last where the intent says first. D2 leaves the board-only problems off `status`. The spec decided both, so I did not raise either as a DECISION.
- The Problems line in the output is about change 149's folder, not this change's code. It is not a CHANGE for 151, and I did not file a PREEXISTING.
- I did not run a factory-run fixture by hand. The tests cover that case.

## Evidence
$ uv run --quiet --script scripts/sdlc.py status | grep -n "^■"
3:■ Planned: 2
10:■ Designing: 0
12:■ Building: 2
18:■ Ready: 0
20:■ Landing: 2
24:■ Unreleased: 39
66:■ Next up: 19
100:■ Release due: 19 changes of minor impact or higher  /sdlc:release
102:■ Problems: 1
105:■ Needs you: 1
exit: 0

$ uv run --group dev pytest -q -n auto -k "status or board"
328 passed, 28 skipped in 21.76s
exit: 0

$ uv run --quiet --script scripts/sdlc.py status | tail -30
(tail shown above: ends with Release due, Problems, then Needs you: 1)
exit: 0

$ cat intent.md; ls . build; tail -15 build/round-1.gate.md; cat checks.md; cat decisions.md
(reads: intent, folder listing, gate record tail ending "Validation passed", decisions D1 and D2; checks.md absent)
exit: 0
