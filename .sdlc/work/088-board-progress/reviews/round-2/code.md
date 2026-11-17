VERDICT: PASS

Both kept changes from round 1 are done.

## Notes

- **Step state in text (`board.html:208`, `:214`):** `STEP_WORDS` puts the state in each pill's text: "✓ " on done steps, "now: " on the current one, "waiting on you: " on a paused one, and nothing on to-do steps. The track now reads without colour or the tooltip.
- **Progress bar (`board.html:221`):** the bar is `aria-hidden="true"` and has no role. The `.meta` line beside it still carries the figure ("18m · ~40m typical · estimate (N runs)"). That line is pushed in the same branch as the bar, so the two always appear together.
- **Tests:** `tests/test_board.py` has assertions on both (the `aria-hidden` bar is one). I ran the file and all 40 tests pass.
- **Not run:** I did not run the full `./check.sh` gate.
- **Done well:** the board only reads and builds nodes with `textContent`. The progress state tests exercise every step via the factory's own writer, which keeps the pinned copy honest.
