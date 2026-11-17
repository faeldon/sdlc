An escalated factory change can now be sent back for another build, and the full gate passes: `./check.sh` ran 1923 tests, all passed, ruff and both plugin validations clean. Everything is left uncommitted in the worktree.

## Slices built
1. **`start` reports a restart without writing anything (R1, R2).** `factory.py start NNN --for build` on a Tier 1 or 2 change at `stage: test` with an ESCALATE decision now returns a `restart` object instead of a refusal. It says what the old decision will be kept as, the round the new build starts at, and the approver's reasons. A READY decision is refused and the refusal names `/sdlc:ship` and `/sdlc-factory:land`. A missing decision, or one that won't read, is refused too. `start` and the new `restart` command share one check, so they can't disagree.
2. **`factory.py restart NNN [--words R<k>]` does the writes (R3, R4).** In order, it:
   - writes `build/round-<R>.restart.md`;
   - renames `decision.md` to `decision-<n>.md`, unchanged byte for byte and never written over (n counts from 1);
   - sets `stage: build`, editing the intent's lines in place.

   It writes nothing outside the change's folder and makes no commit. If a restart was cut short, running it again finishes it.
3. **The loop after a restart (R5, R7, R9, R10).** `verdicts` treats the newest restart record as the new run's first round: it names `build` at that round, then the gate, then review. The round limit counts from the restart, so `limit` reads "6", not "3", after a restart at round 4. A restarted run can still run out of rounds and escalate again. Gate fixes are per round, so the restart round starts at zero. A restart record that won't read stops the run, with `way: rerun`.
4. **Depth (R8).** When deciding whether a run has gone past the light depth's rounds, a round is now counted by its place in its own run. So a light run stays light after a restart, and a full run stays full.
5. **The builder's prompt (R6).** At the restart round the builder is a fresh session. Its prompt names `decision-<n>.md`, quotes the `## Reconsider the approach` section word for word when there is one, and adds the person's words when given. Only the words' id goes on a command line, never the words.
6. **Board (R11).** Needed no code change, as the spec said: a restarted card sits in Build with no decision, and `decision-1.md` is listed and served as one of its files.
7. **Skill and docs (R12, R13).**
   - **Skill:** `build/SKILL.md` covers Step 0, the Step 1 display, a third wording of the Step 2 question, and Step 3 running `restart` (writing the `R<n> (person, restart)` line after the yes). It also gains one new `allowed-tools` rule.
   - **Docs:** `plugins/factory/README.md`, AGENTS.md's factory paragraph and the board line in `docs/REFERENCE.md` are updated.

## Tests added
- **`tests/test_factory.py`:** 15 new test functions, 18 cases with parameters.
  - Every test the spec names is there.
  - Two more came up while building: `test_restart_refuses_to_overwrite_an_archive` and `test_restart_refuses_what_start_refuses`.
  - The new loop tests all failed before the code went in.
  - I undid the R7 and R8 fixes one at a time; each time, its test failed.
- **`tests/test_board.py`:** one new test. It passed before any code change, so it guards the board's current behaviour rather than proving new code.

## Changes to plan.md
I added an "As built" section. It covers two extra fields on the `restart` object, `record` and `under_way` (true for a restart cut short). It also notes that `_rounds_at_depth()` now reads the restart records, and that the board test passed as a pin. The Files list now records the `docs/REFERENCE.md` edit.

## Notes
Nothing left in `notes.md`. The `.sdlc/work/inbox.md` change in the tree was already there when I started; I didn't touch it.

No decisions raised.

## Evidence

$ uv run --group dev pytest -q tests/test_factory.py -k "restart or escalat or not_ready" -n auto   (before the code)
18 failed, 1 passed in 4.57s
exit: 1

$ (R8's fix undone) uv run --group dev pytest -q tests/test_factory.py -k light_run_stays
1 failed, 155 deselected in 3.45s
exit: 1

$ (R7's fix undone) uv run --group dev pytest -q tests/test_factory.py -k round_limit_counts
1 failed, 155 deselected in 0.26s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py -n auto
156 passed in 7.76s
exit: 0

$ uv run --group dev pytest -q tests/test_board.py -n auto
41 passed in 5.88s
exit: 0

$ uv run --group dev pytest -q tests/test_skills.py -n auto
339 passed in 1.94s
exit: 0

$ ./check.sh
All checks passed!
192 files already formatted
1923 passed in 58.28s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py tests/test_board.py tests/test_skills.py -n auto
536 passed in 6.11s
exit: 0

$ uv run --quiet --script scripts/sdlc.py check
■ Problems: 0
    none ✅
exit: 0
