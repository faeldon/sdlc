DECISION: ESCALATE

## Why

The build is finished. Round 3 is `VERDICT: PASS` from code, ui and ux. The gate passed (2254 passed, 13 skipped). Round 2's kept CHANGE about fixture 006 is fixed and pinned by `test_the_board_fixture_stops_as_the_factory_writes`.

I'm escalating for one reason: D5 is still unticked. It asks you which version of outcome 2 the intent should keep. The ux reviewer saw `rerun /sdlc-factory:build 006, or /sdlc:ship 006` take three lines at 390px. The ui reviewer read the same shot as two lines. They disagree on a fact, and you need to decide whether "a line or two" holds before this lands.

## Open items

- None. No CHANGE is open in round 3.

## Decisions to confirm

- **D5:** the build assumes three short lines at 390px are acceptable. It keeps `WAYS["mend"]` as `rerun /sdlc-factory:build {id}, or /sdlc:ship {id}` and would reword the intent's outcome to "in a few short lines, not one run-on sentence". The other option is to drop `or /sdlc:ship {id}`. That would also change `status`'s `→` line and the stop record.

## For the person at ship

1. **D5 first:** look at `.sdlc/reports/shots/120-board-nits/round-3/ux/index-390x844.png` (and the `ui/` copy) at card 006. Decide whether the line counts as two lines or three, and whether that's acceptable. If you accept three, say so in the intent's Outcome before landing.
2. **`plugins/factory/scripts/factory.py`:** check `WAYS`, `WAYS_WHY` and the extra body line in `stop_text()`. That line must not match `STOPPED_RE`, `NEXT_RE` or `PROBLEM_RE`. Watch for conflicts in the `WAYS` block with 112, 113 and 119.
3. **`scripts/sdlc.py`:** check `FACTORY_STOP_NEEDS` and `needs_of()`. Code's round-3 nit says line ~4120 still nests one f-string inside another.
4. **Smaller nits left (code round 3), none carried in `notes.md`:**
   - `tests/test_next_up.py:620-621`: `STOP_NEXT` still holds the old `rerun` sentence, under a comment that is now untrue.
   - The docstring of `test_each_way_on_fits_two_lines_at_phone_width` overstates what the 90-character check proves.
   - D4 (an old stop record keeps its old `NEXT:` line until the next `verdicts --record`) appears in no doc. It belongs in the changelog line.
5. **Wording nit (ux):** "fix its cause" has an unclear "its" in both the `rerun` way and its needs label.
6. **Dark theme:** no shot shows the dark theme, so `--stop` in dark mode hasn't been checked.

- IMPACT: patch — the board and `status` read better: a long next step wraps inside its card, a stop's next step is a short command, and its needs-you line is in plain words. The stop record keeps its `STOPPED:`/`NEXT:`/`- PROBLEM:` shape, so nothing that reads it by machine changes. A stop recorded before this change keeps its old `NEXT:` sentence until its next `verdicts --record`.

## Undone items

`notes.md` has no unticked `- [ ]` items. Its one item, round 2's ux point on fixture 006, is ticked and was done in round 3.

## How to recover

The prompt names no irreversible paths. Per `plan.md`, `git revert` undoes the whole change. A `runs/stopped.md` written by the new `stop_text()` has one extra line of prose, and the old readers ignore it.
