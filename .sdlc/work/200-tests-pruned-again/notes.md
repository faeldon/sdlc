# Notes

> What the build found on the way: the drifted tests looked at again, and what was left out of
> this change.

## The drifted tests, looked at again

The old rule named twelve tests over the last 30 changes (the retrospective showed the top nine).
Under the new one (a test's code is the code its last change touched *that it loads*; a data file
loads nothing; a change too large to pair still counts as a test's last change), one is left:

- `tests/fixtures/close-output.json`, `tests/prompts/land-fix.txt`,
  `tests/prompts/land-checks.txt`, `tests/prompts/train-resolve-deleted.txt`: exact goldens.
  Each is data, compared whole by its test, which fails when close's output or the prompt moves.
  They no longer drift. Kept as they are.
- `tests/test_bugs.py`, `tests/test_next_up.py`, `tests/train_driver.py` (and
  `land-checks.txt`): last touched by 187, a change of more than 50 files that the pairing left
  out, so drift dated each back to 176 or 185. 187 now counts as their last change, and none
  drifts. `train_driver.py` also loads no code itself: it takes `factory` as an argument, and
  the tests that import it load `factory.py`. Kept.
- `tests/test_decision_alternatives.py`, `tests/test_prompts.py`: they load `factory.py`, which
  two later changes moved without them (one short of drifting). They were named before only
  because 196 also touched `landing.py`, which neither loads. Kept.
- `tests/test_indicators.py`, `tests/test_surface.py`: they were named for `retro.py` and
  `.sdlc/setup.json`, which they don't load. Of the code each does load, `indicators.py` hasn't
  moved since and `sdlc.py` moved twice. Kept.
- `tests/test_function_heat.py`: still drifted, and rightly by the rule. It loads `retro.py` by
  path, which seven changes have moved since. It reads only `retro.EVIDENCE_LIMIT`, to check
  that the heat script's output fits under it, and that still holds. Kept as it is. It drifts
  until it is next edited, since the rule can't tell one constant from the whole module.

## The slow tests

Each slow test's setup (`_three()`, `_ready()`) took under a second of its 12–64. The time is
the train's own steps, so sharing a fixture would have saved nothing. Instead:

- `test_every_ejection_names_its_cause` is removed. Its three trains proved what the `train
  --run` tests already prove: `gate` (`test_train_run_ejects_a_gate_fault_and_lands_the_rest`),
  `review` and `--eject` keeping it (`test_train_run_stops_at_a_kept_change_and_resumes`), and
  `refusal` (`test_train_run_stops_at_a_refusal`). The mutations in the build report show each
  cause's test failing.
- `test_train_run_resumes_after_a_kept_change` is folded into
  `test_train_run_stops_at_a_kept_change_and_resumes`, and `test_train_run_lands_a_batch_of_three`
  into `test_a_killed_train_run_resumes`. `test_a_train_stops_past_land_moves` is folded into
  `test_a_move_mid_train_re_stacks_the_rest_and_counts_once`, which now runs under `[land]
  moves = 1`: B lands after the first move, and the second move stops the train before C closes.
- `test_a_train_fix_already_made_goes_on_to_the_gate` keeps its `train --run` half and reads the
  step order (fix, gate, review) from the loop's progress lines.
- `test_land.py`'s batch test lands two changes, not three: one holds the checks and the note,
  the other the irreversible path.

## Left out

- [x] The train's reading runs about 1,500 git calls for a driven train of three (723 → seed: 2026-11-20-50
  `rev-parse`, 418 `show`), which is most of each train test's time and of a real landing's
  bookkeeping. Caching what doesn't change within one reading would speed both.
- [x] No test fails when the train's readiness refusal (`_land_readiness()`'s `refusal`, in → seed: 2026-11-20-51
  `cmd_train`) is ejected under another cause: mutating its `"refusal"` to `"review"` passed
  every train and landing test. The removed `test_every_ejection_names_its_cause` never reached
  that path either: its stray file is the `failed` path, which `test_train_run_stops_at_a_refusal`
  covers.
