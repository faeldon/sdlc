I built change 154: in a landing train, the person's `yes, with a fix` now runs as soon as its change is in place, before the first gate. The full gate passes (2832 tests, 28 skipped), and the work is left uncommitted for `/sdlc:ship`.

## Slices built
I wrote `plan.md` because this Tier 1 change touches four files. The build followed it.

1. **The fix comes before the gate.**
   - `_train_reading()` now names `fix` for the change with a stored fix that hasn't been made, as soon as that change is in place. That covers three cases: it was stacked, it was committed and never moved, or its conflict was resolved. The old step that put the fix just before the change's close is removed.
   - Once the fix is amended in, the existing `_tree_changed()` branch takes the new commit, so the changes above stack on the fixed one and the first tip gate sees the fix.
   - `cmd_land_fix --ask` used to refuse while a landing round was open and not yet passed. Now, if that round has no reviewer reply and no ask yet, the fix goes into that same round instead of opening `land-<n+1>`. So that round's review sees the fix and runs every reviewer at the run's depth. A round that already has a reply still refuses until it passes.
2. **The docs say the new order.** The `cmd_train()` and `cmd_land_fix()` docstrings and the comment in `_train_begin()` are updated. In `skills/land/SKILL.md`, the `fix` bullet now says it comes once the change is stacked, after a conflict is resolved and before any gate, and the yes text says the fix comes "before it is gated". `RUN_STEPS` itself didn't need to change: the loop just takes whatever step the reading names, so it now follows the new order.

## Tests
- **New:** `test_a_fix_the_gate_needs_is_made_before_the_gate`. The check fails until change one's file says `AA`, and the stand-in builder's fix writes it. The reading names `fix` before any gate is recorded. The loop ends `done` with both changes landed and none ejected, the fix is in change one's own commit, and the tip is gated exactly once. Before the code change it failed as expected: the reading named `gate` before `fix`.
- **Updated:** `test_train_run_makes_the_stored_fix_once`. It now expects the tip to be gated once, not twice, because the fix is in before the first gate.
- **Updated:** `test_a_fix_commit_needs_an_ask`. A round with an unpassed reply still refuses the ask; once that reply is gone, the same open round takes the fix.

`notes.md` is not written; nothing was left over.

## Decisions
- DECISION: [default] For a change that conflicts when stacked, the fix comes after the conflict is resolved, not before the stack. Going ahead with that unless told otherwise.
  - OPTION: after the resolution — the builder fixes the change as it really sits in the stack, and the train needs no new step; the person's words are applied to code that was just resolved
  - OPTION: before the stack — the fix is on the original change; the stack then re-runs and could conflict again on what the fix touched
  - WHY: the reading already takes the resolution first, and the fix should be gated on the commit that will actually land
- DECISION: [default] The fix always comes before the gate; there is no way for the person to ask for it after the gate. Going ahead unless told otherwise.
  - OPTION: always before the gate — one rule, and the fix is always gated and reviewed in the same round
  - OPTION: let the person choose before or after — covers a fix aimed only at what the landing review would raise; adds a second answer to the yes and a second place the fix can fall
  - WHY: a fix after the gate is exactly the case that got skipped (147's landing); a fix aimed at the review is still reviewed when it comes first

## Evidence

$ uv run --group dev pytest -q tests/test_train.py -k "fix_the_gate_needs"
E       assert ('gate', '002-bb') == ('fix', '001-aa')
1 failed, 43 deselected in 4.33s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_train.py tests/test_land.py
123 passed in 128.46s (0:02:08)
exit: 0

$ ./check.sh
2832 passed, 28 skipped in 569.95s (0:09:29)
✔ Validation passed
exit: 0
