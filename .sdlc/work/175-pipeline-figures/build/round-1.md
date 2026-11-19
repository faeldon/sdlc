`retro` now gives a `pipeline` key with the gate, train and review figures, and both nits are fixed. The full gate is green: 3253 passed, 29 skipped. Everything is uncommitted on the change's branch.

**Slices built**
1. **Nits (R13, R14).** `_none_reason()` now uses `(\s+[^\s=]+=\S*)+$`. `autonomy_counts()` has a comment saying why only default lines are checked for the `SUPERSEDED` and `SETTLED` marks.
2. **`Waited:` (R3).** `factory.py gate` and `sdlc.py gate` now write each attempt's slot wait right after `Seconds:`. The hand gate's line-for-line shape test masks `Waited:` the way it masks `Seconds:`.
3. **`DEPTH:` (R6).** `step_text()` writes `DEPTH: full|light`, and both `read_step()`s return `depth`.
4. **Shared names (R9, R10).** `WAITED_RE`, `DEPTH_RE`, `TRAIN_GATE_RE`, `LAND_TRAIN` and `LAND_ACCEPT` are now in both `factory.py` and `factory_records.py`, under the same names. `LAND_TRAIN` moved out of `landing.py`, which now reads `factory.LAND_TRAIN`, and `accept_path()` builds from `LAND_ACCEPT`. `factory_records.py` also gains `read_gate_attempts(text)` (it reads `waited`) and `resolved_files(text)`. `sdlc.conflicts_resolved()` now goes through `resolved_files()`, so `conflicts.md` is parsed by one rule.
5. **The figures (R1, R2, R4, R5, R7, R8, R11, R12).** A new `pipeline_counts(show, listing)` in the records module returns one change's raw figures. `retro._pipeline()` builds `gates` (this window and the previous one), `red_gate`, `landing`, `depth`, `unreviewed`, `factory`, `by_hand` and `changes`. There is no `mends` key. `lead_view()` and the new figures share one `_p85()` helper. `_previous_window()` is computed once. `pipeline.changes` is printed only with `--metrics`.
6. **Docs (R15).** `docs/REFERENCE.md` *Retrospectives* describes `pipeline`. In `docs/RETRO-SCORECARD.md` the Speed diagnostics and risk exposure rows are updated, and S10 is marked done in wave 3. The factory README and `factory.py`'s docstring name `Waited:` and `DEPTH:`.

**Tests added**
- **`test_retro.py`:**
  - R1 and R12: every `n` is 0 and every rate, share, median and percentile is null in a window with no factory change.
  - R2: medians and 85th percentiles by window; an attempt without `Waited:` counts in `seconds.n` only; the hand gate is excluded.
  - R4: one red-then-green build and one green build give a rate of 0.5.
  - R5: a red tip two changes share counts as one bisection; `ejections.gate == 1`; base moves, accept stops and conflicts.
  - R7: one full and one light run give share 0.5 with n 2, and the older run is missing.
  - R8: one landing of each `unreviewed=` kind.
  - R11: `pipeline.changes` appears only with `--metrics`.
  - R13: two tests for `_none_reason()`.
- **`test_factory.py`:** every gate attempt records `Waited:` (R3); a step record names its depth (R6).
- **`test_train.py`:** `TRAIN_GATE_RE` reads every `GATE:` line `train_record()` writes, and `landing.py` no longer defines `LAND_TRAIN` (R10).
- **Updated existing tests:** `test_board.py` (the `read_step()` pin now checks `depth`), `test_modules.py` (the new names and record files), `test_hand_gate.py` (masking), and `test_retro_prints_each_change_s_numbers_only_when_asked` (it drops `pipeline.changes` the way it drops `cost.changes`).

**Changes to `plan.md`.** I wrote it after reading the code. Its *As built* section records where the build departed from the plan:
- **R13's timing test** runs in a child process with a timeout, not a thread as the spec says. Python's regex engine never lets another thread run while it matches, so a thread's `join(timeout)` can't fire. The first red run did hang for the whole minute.
- **`unreviewed`** has coverage, with `unreviewed not recorded` for landings from before the field.
- **`bisections`** is `{"total": n}`.
- **`CONFLICTS`**: the records module's copy is pinned to `sdlc.CONFLICTS`.

The spec's history check holds: every factory change closed from 166 to 179 has its step, landing step, landing times and train records at its own commit. On this repo, `retro` gives `depth` 0 of 24 measured and `wait.n` 0, so those figures start out missing, not zero, as intended.

**`notes.md`:** nothing left.

- DECISION: [default] For `unreviewed`, a factory landing whose `Sdlc-Landed` has no `unreviewed=` field is counted as missing (`unreviewed not recorded`) and left out of `n`, not counted as `none`. Going ahead with this unless told otherwise.
  - OPTION: missing — follows the intent's rule that a figure the records don't hold is missing, never zero; `n` is smaller.
  - OPTION: count it as `none` — larger `n`, but it claims every path was reviewed when nothing recorded that.
  - WHY: the intent's constraint that an older change's absent figure is missing, never zero.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q tests/test_retro.py -k none_reason   (before the fix)
FAILED tests/test_retro.py::test_none_reason_returns_quickly_on_many_equals_tokens
1 failed, 1 passed, 189 deselected in 60.42s (0:01:00)
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k none_reason
2 passed, 189 deselected in 0.10s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py -k slot_wait   (before the writers)
FAILED tests/test_factory.py::test_every_gate_attempt_records_its_slot_wait
1 failed, 386 deselected in 4.24s
exit: 1

$ uv run --group dev pytest -q -n auto tests/test_hand_gate.py
49 passed in 5.61s
exit: 0

$ uv run --group dev pytest -q tests/test_factory.py tests/test_board.py -k "runs_depth or step_record_is_a_pinned"   (before DEPTH:)
FAILED tests/test_factory.py::test_record_writes_the_runs_depth
FAILED tests/test_board.py::test_the_step_record_is_a_pinned_copy - KeyError
2 failed, 1 passed, 696 deselected in 1.71s
exit: 1

$ uv run --group dev pytest -q tests/test_factory.py tests/test_board.py -k "runs_depth or step_record_is_a_pinned or record_writes"
6 passed, 693 deselected in 4.29s
exit: 0

$ uv run --group dev pytest -q tests/test_train.py -k cores_train_gate   (before the copies)
FAILED tests/test_train.py::test_the_cores_train_gate_copy_reads_every_gate_line
1 failed, 82 deselected in 0.27s
exit: 1

$ uv run --group dev pytest -q tests/test_train.py -k cores_train_gate
1 passed, 55 deselected in 0.15s
exit: 0

$ uv run --group dev pytest -q tests/test_retro.py -k pipeline   (before _pipeline)
7 failed, 191 deselected in 16.10s
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -k "pipeline or lead"
10 passed, 188 deselected in 19.73s
exit: 0

$ uv run --group dev pytest -q -n auto tests/test_modules.py tests/test_feature_map.py tests/test_windows.py
74 passed in 3.19s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 175   (first full run)
FAILED tests/test_retro.py::test_retro_prints_each_change_s_numbers_only_when_asked
1 failed, 3252 passed, 29 skipped in 183.36s (0:03:03)
exit: 1

$ uv run --group dev pytest -q tests/test_retro.py -n auto
198 passed in 46.36s
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro | python3 -c "...print pipeline keys..."
['by_hand', 'depth', 'factory', 'gates', 'landing', 'red_gate', 'unreviewed']
{'measured': 0, 'of': 24, 'greyed': True} {'n': 0, 'median': None, 'p85': None} 24 {'total': 3} {'builds': 28, 'red': 1, 'rate': 0.04, 'n': 28}
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 175
All checks passed!
313 files already formatted
3253 passed, 29 skipped in 276.59s (0:04:36)
✔ Validation passed
exit: 0
