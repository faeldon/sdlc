The landing track is built and the full gate passes (2377 passed, 13 skipped). Nothing is committed. The change touches 8 files plus one new fixture change. I wrote `plan.md` first and updated it at the end to match what was built.

## Slices built

1. **A step record for the landing, `runs/land-step.md`.** It is a separate file from `runs/step.md`, which keeps the build's shape untouched. It holds the step, the landing round, how often the base branch has moved so far, the `[land] moves` limit and the start time. A stop adds the step it stopped at and one line per problem. The start time is kept while the step and round stay the same, so reviewers started together share one start.
2. **Each landing command records its step as it starts:**
   - `land` records `ship` before `sdlc.py ship` stages every path, or `rebase` before the earlier record is amended in on a second landing. Either way the record goes into the change's commit and `sdlc.py base` still finds a clean tree.
   - `gate --land` records `gate` before it hashes the tree.
   - `agent` records `resolve`, `fix`, `review`, `verify` or `mend` once nothing is left to refuse.
   - `land --close` records `close` before the amend, so it lands in the commit that close merges.
   - Refusals of `land`, `resolve` and `land --close` record a `stop` with the reason.
   - `land-verdicts --record` records a `stop` with its problems. Without `--record` it writes nothing, as before. The land skill now passes `--record`.
   - `resolve --continue` stages the record along with the costs line, because the builder's session writes it mid-rebase.
3. **The board reads it.** For a change at `test` or `shipped` with that file, the card shows a landing track: ship → rebase (or resolving / fixing) → gate → review (or mending) → verify → close. It shows the landing round, the moves so far, and a stop marked at its step with its problems. The card stays in Ready to ship before the commit and Ready to close after. At `build` the file is ignored. A record that can't be read is listed as a problem on the card.
4. **Timing.** History now gives typical times for the landing's gate, review and verify: the cost rows after the approver, plus `build/land-*.gate.md`. The other landing steps show elapsed time only.
5. **The page and the fixture.** The track row is labelled `landing L<n>`, with "base moved m of k times", a `stopped` step state said in words, and "landing stopped: …" flags. New fixture change `012-draft-publish` is shipped, with its landing review under way.
6. **Docs:** `factory.py` docstrings, `board.py`'s docstring, `docs/REFERENCE.md` and the factory README.

## Tests added

- **`tests/test_land.py`:**
  - Every step is recorded through a landing that has to rebase twice, and `land`'s and `close`'s records end up in the commit with the tree left clean.
  - The builder's `resolve` step goes into the rebased commit.
  - A failed gate records a stop via `land-verdicts --record`, and a plain reading writes nothing.
  - Running out of allowed moves records the stop.
  - The record reads back what was written.
- **`tests/test_board.py`:**
  - The track for each of the nine steps.
  - A landing shown in Ready to ship.
  - A stopped landing.
  - The record counts only at `test` or `shipped`, and a garbled one is a problem.
  - The board's copy of the parser is pinned to `factory.py`'s.
  - Landing typical times.
  - The page labels.
  - The fixture's record and its landing card.

## Changes to `plan.md`

- `resolve` writes no step of its own. An earlier version recorded `gate` after it, which broke an existing test: a rebase where only the counter conflicts must leave the tree clean. `gate --land` records the gate itself.
- `accept` records no step.
- The test names were updated to the ones written.

## Left in `notes.md`

- A shipped card still names `/sdlc:close` as its next step while it is landing.
- A stopped landing doesn't move to Needs you.
- `accept` records no step.

- DECISION: [default] Keep the landing's record in its own `runs/landing-step.md`, or add landing steps to `runs/step.md`? Options: own file; extend `runs/step.md`. Going ahead with its own file (named `runs/land-step.md`): the constraint keeps the build's record as it is.
- DECISION: [default] Should each landing command write its own step as it runs, or should only `land-verdicts --record` write it? Options: each command; only `land-verdicts`. Going ahead with each command, plus `land-verdicts --record` for stops: that shows the gate and the reviews while they run.
- DECISION: [default] Time which landing steps against history? Options: gate, review and verify; elapsed time only. Going ahead with gate, review and verify (from the rows after the approver and `build/land-*.gate.md`); the rest show elapsed time only.
- DECISION: [default] Should a just-landed card stay a while as "landed", or disappear? Options: stay briefly; disappear. Going ahead with disappear: close removes the folder, and the board writes nothing to keep it.
- DECISION: [default] Should a stopped landing move its card to Needs you? Options: keep the column; move to Needs you. Going ahead with keeping the column and showing the stop on the card: moving it would change `sdlc.needs_of()`, which `status` shares, and that is outside this change's files.

## Evidence

$ uv run --group dev pytest -q tests/test_land.py -k "step or records or stopped_landing or past_its_moves"
FAILED tests/test_land.py::test_the_landing_step_record_reads_back_what_it_writes
5 failed, 2 passed, 54 deselected in 37.19s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_board.py
14 failed, 139 passed, 13 skipped in 13.16s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_land.py tests/test_board.py
216 passed, 13 skipped in 18.50s
exit: 0

$ ./check.sh
All checks passed!
2377 passed, 13 skipped in 58.81s
✔ Validation passed
exit: 0
