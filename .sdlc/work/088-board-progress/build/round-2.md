Both round-1 changes the verifier kept are fixed, and the full gate passes with 1902 tests. Both changes are in `scripts/board.html` only. Nothing is committed.

- **ux C1 (a step's state was shown only by colour and a tooltip):** each step now says its state in its own text. A finished step reads "✓ build", the running one "now: reviews 2/4", a paused one "waiting on you: reviews 1/4", and a step still to come shows just its name. The wording lives in one place in the page, `STEP_WORDS`. I removed the `title` tooltip, since the text now carries the state. The colours and borders are unchanged and back up the text.
- **ux C2 (the progress bar sat inside the card's button, so screen readers lost it):** the bar no longer claims to be a progress bar and is hidden from assistive tech (`aria-hidden="true"`). The line under it always says the same in words when the bar is shown: "18m · ~40m typical · estimate (k runs)". Its width still comes only from `progress.fraction`.

I added one test, `test_a_step_s_state_is_in_its_text_and_the_bar_is_hidden_from_assistive_tech`. It failed before the edit and passes now. It checks that the done, running and paused states each have their own words, that the page never sets a progress-bar role, and that the bar is hidden.

`plan.md` is unchanged, since both fixes sit inside the page slice it already describes. Nothing was added to `notes.md`. I raised no new decisions this round.

## Evidence

$ uv run --group dev pytest -q tests/test_board.py -k assistive   (before the fix)
1 failed, 39 deselected in 0.07s
exit: 1

$ uv run --group dev pytest -q tests/test_board.py
40 passed in 11.78s
exit: 0

$ ./check.sh > /tmp/088-gate.log 2>&1; echo "exit: $?"; grep -E "passed|failed|All checks|Validation passed" /tmp/088-gate.log | tail -4
exit: 0
All checks passed!
1902 passed in 38.94s
✔ Validation passed
✔ Validation passed
exit: 0
