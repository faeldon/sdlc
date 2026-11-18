# Plan — 154 landing fix before gate

> Tier 1, written because the Approach touches the script, the land skill and two test files.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `_train_reading()`: in step 2 (each change stacked), once a change sits where the train wants
    it (stacked, or committed in place when it never moved, or its conflict resolved), name `fix`
    for it when the train's stored fix is its and not `done`; drop step 5's before-close `fix`.
    The existing `_tree_changed()` branch then takes the amended commit as `stacked`, so the
    changes above re-stack on it, and the first gate reads the fixed tip.
  - `cmd_land_fix()` `--ask`: today it opens `land-<n+1>` only when round `n` passed. A stack
    opens round `n` itself (and `_fresh_round()` for a change in place), empty, before any gate
    or reviewer; the ask now goes into that round when it is untouched (no reply in
    `reviews/land-<n>/`, no ask yet), so the round's review reads the fix at the run's depth
    (`land_verdict()`'s `fixed`). A round with a reply that hasn't passed still refuses.
  - `cmd_train()`'s docstring, the `RUN_STEPS` comment and `_train_begin()`'s comment: where the
    fix falls. `RUN_STEPS["fix"]` itself is unchanged (`--ask`, the builder, `--commit`).
  - Reused as they are: `_train_fix()`, `read_fix_words()`, `land_ask()`, `_amend_record()`,
    `_tree_changed()`, `land_round()`.
- `plugins/factory/skills/land/SKILL.md`: the `fix` bullet says the fix comes once the change is
  stacked (after a conflict's resolution), before the tip's gate.
- `tests/test_train.py`, `tests/test_land.py`.

## Work order

1. **The fix before the gate, in a train.** Red: a new test in `tests/test_train.py`, a train of
   two whose `[commands] check` fails until change one's file says `AA`, begun `--by person
   --fix 001=R1`, the stand-in builder writing `AA`: the loop ends `done`, both land, none
   ejected, the fix in one's commit, and the first gate on the tip already green. Green: the
   reading change and the `--ask` round reuse. Then update the existing
   `test_train_run_makes_the_stored_fix_once` (the tip is gated once now, not twice) and
   `test_a_fix_commit_needs_an_ask` (an empty open round takes the ask; a round with a reply
   that hasn't passed refuses).
2. **The skill and the docstrings** say the new order.

## Tests

- `test_a_fix_the_gate_needs_is_made_before_the_gate` (new): Outcome 1 and 2 — the fix step is
  named right after the stack, before the first gate; the change lands, never ejected.
- `test_train_run_makes_the_stored_fix_once` (updated): made once, reviewed at depth, the tip
  gated once (the fix is in before the first gate).
- `test_a_fix_commit_needs_an_ask` (updated): `--ask`'s round rule.

## Rollback

Nothing outside git: `git revert` undoes it. A train under way with a stored fix not yet made
simply takes it at its next reading.
