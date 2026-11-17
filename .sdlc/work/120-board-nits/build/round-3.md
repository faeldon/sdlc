I updated the board fixture that the review screenshots are built from. Card 006 now shows the short next step instead of the old long sentence. The full gate passes: 2254 tests passed, 13 skipped. Nothing is committed.

**Plan first** (`plan.md`). The escalation pointed out that the plan never covered this fixture, so I added:
- **Files to change:** `tests/fixtures/board/changes/006-draft-purge/runs/stopped.md`, with the reason. It was written before this change, so no screenshot could show outcome 2 (a stopped run's next step reads in a line or two at phone width).
- **Work order:** a slice 6 for the fixture. It also notes D4: a real host's old stop record keeps its old sentence until its next `verdicts --record`, because the board writes nothing.
- **Tests:** a line linking the new test to outcome 2 as the reviewers see it.

The rest of the plan and the code are unchanged.

**Slice 6, the fixture:**
- **Red:** the new test `test_the_board_fixture_stops_as_the_factory_writes` in `tests/test_board.py` checks that every `runs/stopped.md` in the board fixture matches exactly what `factory.stop_text()` writes now for the same way and problems. It failed on 006 for the expected reason: the old sentence with "mend" in it, against the current short line and its explanation.
- **Green:** I rewrote 006's record by calling `stop_text("006-draft-purge", "mend", [...])` itself, not by hand. Its `NEXT:` line now reads `rerun /sdlc-factory:build 006, or /sdlc:ship 006`, and the longer sentence sits in the record's body.
- **What the test proves:** the fixture can no longer fall behind a later change to the `WAYS` wording, which is how the screenshots went stale for two rounds.

**Open items from the escalation:**
- **The ux reviewer's CHANGE** (the old `NEXT:` line in fixture 006): fixed as above. I ticked the line in `notes.md` and noted the fix there. The next screenshot round will show the short line at 390px; I haven't taken new screenshots myself.
- **D1–D4:** you confirmed them all, and they're ticked in `decisions.md`. I built on them as they stand.
- **D4's changelog line:** the escalation suggested one, but I didn't add it. It belongs in the impact line written at ship: an existing stop record keeps its old `NEXT:` wording until its run is checked again with `verdicts --record`.

Nothing new was left in `notes.md`.

No decisions raised this round.

## Evidence

$ uv run --group dev pytest tests/test_board.py::test_the_board_fixture_stops_as_the_factory_writes -q   (before the fixture edit)
E             + uild 006, whose one mend asks again for the missing ## Evidence or a verdict on the reply's first line; if that reply still lacks it, ship it by hand with /sdlc:ship 006
E             - uild 006, or /sdlc:ship 006
FAILED tests/test_board.py::test_the_board_fixture_stops_as_the_factory_writes
1 failed in 0.23s
exit: 1

$ uv run --group dev pytest tests/test_board.py -q -k fixture
2 passed, 143 deselected in 6.21s
exit: 0

$ ./check.sh
All checks passed!
264 files already formatted
2254 passed, 13 skipped in 154.65s (0:02:34)
✔ Validation passed
exit: 0
