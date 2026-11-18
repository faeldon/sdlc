VERDICT: CHANGES

- CHANGE: scripts/board.py:730: a landing stopped at `close` sits on a card already at `stage: shipped` (the ship commit is in), but `next_action()` tells the person to run `/sdlc:ship <id>` by hand. Ship has already run, so that step misleads. For a stopped landing at `shipped`, name `/sdlc:close <id>` (or `/sdlc-factory:land <id>` to resume), and keep `/sdlc:ship <id>` for a stop before the ship commit.
- DECISION: [default] The landing track's `accept` step (acceptance checks run in the landing, after the gate) is not recorded, so while they run the card keeps showing the gate as "now". The inbox already carries a step for `accept` as later work. Recommend keeping it deferred: the step record is the factory's, and `accept` is a separate command with its own record. Settled here only if the person agrees it can wait.

## Notes

**What I read.** I had no shell in this session, so I could not run `git diff 947b947...HEAD` or the tests. I reviewed the current tree at HEAD instead: both screenshots (1280×800 and 390×844), `intent.md`, `build/land-2.md`, `decisions.md` (D1–D6, all decided), `scripts/board.py` (`_progress`, `_land_progress`, `read_land_step`, `next_action`, the `LAND_*` tables), `scripts/board.html` (`progressRow`, `card`, and the step and stop styles), the factory's `_record_land`, `land_step_text`, `land_verdicts` and `read_land_step`, the land skill's step 2 to 4 text, and the 012 fixture's `runs/land-step.md`. I did not render any state myself; the screenshots are the only rendering evidence.

**What the screenshots show.** Card 012 sits in Ready to close with its landing track: `landing L1`, ✓ ship, ✓ rebase, ✓ gate, `now: review`, verify, close, and "base moved 1 of 3 times". Each state is labelled in words, not colour alone. The stop style is a red left border plus a `stopped:` step and a `landing stopped:` line. The 390px view keeps one column per card, the track wraps, and the card stays a single button, so it is reachable by keyboard. The 390px shot shows only the Needs you column, so I could not see a landing card at phone width.

**States I could not see.** The 012 fixture has an empty `SINCE:`, so its card shows no "so far" time. A real landing record always writes `SINCE:` (`_utc_now()`), so this is a fixture gap, not a product one. I did not judge the elapsed line from it. I also could not see a stopped landing card or a landing at `shipped` on screen; I judged those from `next_action()` and `progressRow()`.

**Smaller findings:**
- `next_action()` (board.py:737) reads "the factory is landing it, at resolve" or "at mend": the raw step names. Consider the labels the track already uses ("resolving", "mending").
- `_land_progress()` (board.py:505) falls back to `LAND_AT` index 0 when a stop has no `AFTER:` line, so the first step ("ship") would show as stopped. Only a malformed record reaches it, but the stop would point at the wrong step.
- A stop recorded with no problem lines shows a stopped step with no reason. `_record_land` callers in the current code always pass one, so this only applies to a future caller.
- `plugins/factory/README.md` line 381 runs past the length the other lines keep. Docs only; no effect on the person.
- D6 (the landing that goes back to `rebase` after a base move) is settled and I did not reopen it.

**What the change does well.** The track is one row shared with the build's, with the same words and the same `now:` / `✓` / `stopped:` vocabulary. A landing shows in all three columns it can sit in, and a stopped landing keeps its column rather than being moved into Needs you, so the board's column rules don't change. The board still writes nothing, and every node is built with `textContent`.
