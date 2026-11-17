The rebase conflicts are resolved in all four files and the gate is green (2173 passed). Every conflict was additive, so I kept both sides in each file and ran no git command.

- **`.sdlc/work/inbox.md`:** kept the base branch's seeds 63–68 and this change's 69–70; the ids don't clash. I put back the `Raised 2026-11-17.` line that seed 68 lost at the conflict boundary, so 68, 69 and 70 each end with one.
- **`scripts/sdlc.py`:** kept both sides in the factory parsing section.
  - From the base branch: `FACTORY_STEP`, `FACTORY_STEP_RE`, `FACTORY_ROUND_RE`, `FACTORY_AGENT_TIMEOUT` and `factory_first_build()`.
  - From this change: `FACTORY_RECONSIDER`, `GARBLED_LEDGER`, `factory_reading()`, `needs_of()` and `answered()`.

  The base branch's code comes first, then this change's.
- **`tests/test_metrics.py`:** kept the base branch's new pin asserts and its new test on superseded ledger lines. This change's `FACTORY_RECONSIDER` pin goes right after those asserts, inside the same test, rather than after the new test.
- **`tests/test_board.py`:** kept the base branch's `FIXTURE` and `test_the_board_fixture_shows_every_card_state`, then all of this change's tests. Both need imports (`shutil` and `sys`), and both are present.

The one place the two sides could have clashed was the base branch's fixture test, which expects an escalated change at `test` to sit in Needs you. It ran (not skipped) and passed. Its escalated card, `008-draft-import`, has no `decisions.md`, so this change's rules keep it in Needs you as `read the escalation`.

## Evidence

$ grep -nE "^(<<<<<<< |=======$|>>>>>>> )" .sdlc/work/inbox.md scripts/sdlc.py tests/test_board.py tests/test_metrics.py; echo "markers left: $?"
markers left: 1
exit: 0

(grep's 1 means it found no markers.)

$ ./check.sh
All checks passed!
2173 passed, 9 skipped in 51.86s
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_board.py::test_the_board_fixture_shows_every_card_state -rs
1 passed in 1.62s
exit: 0
