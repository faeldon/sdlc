I built change 104: the landing now follows `main` when it moves before the close, and a fix asked for at landing goes to the change's builder and its reviewers. The full gate passes (2018 tests). Everything is uncommitted and `HEAD` is still `473bfe1`. Every new test failed first for the reason I expected, then passed.

## Slices built

1. **The bound on following main (R5's config half):** `[land] moves`, default 3, read from the base branch beside `auto` and `batch`. A bad value gives a warning and the default.
2. **Following main (R1–R5):**
   - Before closing, `land --close` counts how far the base branch is ahead (`_behind()`). If it moved, it records the move in `runs/land-moves`, amends the record into the change's commit through 097's `_amend_record()`, and returns `state: moved` with `moves: <k>`.
   - If `sdlc.py close` itself refuses, it counts the base again. When the base moved and close's `done` is empty, it also returns `moved`, without reading close's wording.
   - Once `moves` moves are recorded, it refuses with the spec's wording.
3. **What no review read (R13, R14):** `land_unreviewed()` compares the change's files with the snapshot of the newest complete build round, leaving out the change folders.
   - A path that differs, or a missing snapshot, is a signal at `land` and `land-check`, so `--by auto` is refused.
   - `land_message()` adds `unreviewed=<n|unknown>` to `Sdlc-Landed` and puts the paths in the body.
4. **Measure carries the field (R15):** `metrics.landed_unreviewed()` copies it to `Sdlc-Totals`, and `sdlc.py`'s measure calls it.
5. **A fix asked at landing (R8–R12):**
   - `factory.py land-fix --ask` opens a new landing round and writes `build/land-<n>.ask.md`.
   - `agent --task land-fix` resumes the change's builder with the person's words.
   - `land-fix --commit` amends the builder's edits into the change's commit through `_amend_record(..., also=)`.
   - `land_verdict()` then asks for every reviewer at the run's depth and reports `fixed`.
   - The fix stays a signal for the rest of the change's life, at `land` and at `land --close`.
6. **The skill and docs (R6, R7, R16):**
   - The land skill gets the `land-fix` rule, reads `land.moves`, and asks the new question with four answers.
   - It gains a Step 3.4 for the fix; the close moves to 3.5, which handles `moved`.
   - The factory README and `docs/REFERENCE.md` *Metrics* describe the follow loop, the fix, and `unreviewed=`.

## Tests added

All new tests are in `tests/test_land.py` unless named otherwise.

| Test | Proves |
|---|---|
| `test_main_moving_before_close_sends_the_landing_back_to_its_rebase` | R1–R3: `moved`, the round-1 review and `runs/land-moves` in the commit, then round 2 (gate, behaviour review, pass), then the `Close` commit |
| `test_a_move_racing_close_reads_as_moved` | R4, with `_sdlc` stubbed |
| `test_a_landing_stops_after_land_moves_moves` | R5's bound |
| `test_the_bound_on_following_main_is_the_base_branchs` | R5: the change's own `moves = 10` is ignored, and a bad value gives a warning |
| `test_a_hand_edit_after_the_approver_is_a_signal_and_recorded` | R13, R14, including `parse_trailers(...)["landed"] == {"by": "person", "unreviewed": 2}` and the `unknown` case |
| `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth` | R8–R11 |
| `test_a_fix_commit_needs_an_ask` | R8, R10 |
| `test_a_fix_at_landing_is_never_landed_by_auto_later` | R12 |
| `tests/test_metrics.py::test_a_landing_with_unreviewed_paths_carries_them_to_totals` | R15 |

Two existing tests changed:
- `tests/test_skills.py`: `READS_CONFIG["sdlc-factory:land"]` gains `factory.land.moves`.
- `tests/test_factory.py::test_config_defaults_and_its_warnings`: it lists every default, so the new `"moves": 3` had to go into it.

097's `test_a_landings_record_never_takes_in_a_path_outside_its_folder` and `test_a_landed_commit_says_who_passed_its_gate_and_carries_no_review_count` pass unedited. One other 097 test needed a one-word edit; see the first decision below.

## Changes to `plan.md`

I wrote it before any code. Where the build departed from it, I updated it:
- **Order in `land --close`:** 097's `by=auto` check stays first, as 097 wrote it, and the move check comes after it. The amend still carries the move's line (R2).
- **Signatures:** `metrics.landed_unreviewed(summary, tip)` takes the parsed tip trailers. `land_signals()`'s `unreviewed` keyword defaults to `()`, so 097's callers are unchanged.
- **New helpers:** `_unreviewed_at_test()`, `land_ask()` and `land_ask_path()`.

## Left in `notes.md`

- [ ] `land-fix --ask "<words>"` passes free text through a shell argument, as R8 says. Everywhere else, the person's words reach an agent through `decisions.md`. Because this item is unticked, `land-check` will leave 104 out of a batch, so 104 itself ships by hand.

## Decisions

- DECISION: [default] R13's "no snapshot" signal would refuse `--by auto` in every 097 test, because the `_ready()` fixture left no review round. Keep the spec's signal and make the fixture faithful, or drop the no-snapshot signal? Options: fixture leaves a reviewed round; drop the signal for changes with no rounds. Going ahead with the first: `_ready()` now leaves one snapshotted round that every reviewer passed, as a real factory run does. The one 097 test that needs no round (`test_a_resolution_the_build_reviewed_is_no_signal_and_one_after_it_is`) passes `reviewed=False`; no other line of an existing test changed.
- DECISION: [default] In `land --close`, run 097's `by=auto` check before the move check, against the Design's order? Options: 097's order; the Design's order. Going ahead with 097's order: 097's code stays untouched, and the amend still carries the move (R2).
- DECISION: [default] What does a commit with `unreviewed=unknown` say in its body? Options: "No snapshot of its last review."; nothing. Going ahead with "No snapshot of its last review.", since the spec words only the line for paths.

## Evidence

$ ./check.sh > /tmp/104-gate.txt 2>&1; echo "exit: $?"; grep -E "passed|failed|All checks|files already|Validation" /tmp/104-gate.txt
exit: 0
All checks passed!
208 files already formatted
2018 passed in 47.25s
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q -m portable 2>&1 | tail -1
216 passed, 1802 deselected in 57.40s
exit: 0

$ uv run --group dev pytest -q tests/test_land.py tests/test_metrics.py tests/test_skills.py tests/test_factory.py 2>&1 | tail -1
640 passed in 74.85s (0:01:14)
exit: 0

$ uv run --group dev pytest -q tests/test_land.py -k "moving or racing or land_moves or bound_on" 2>&1 | tail -15   (red, before the code)
E       KeyError: 'moves'
4 failed, 17 deselected in 4.44s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py 2>&1 | tail -4   (red, R13/R14 test before the code)
FAILED tests/test_land.py::test_a_hand_edit_after_the_approver_is_a_signal_and_recorded
1 failed, 21 passed in 24.80s
exit: 1

$ uv run --group dev pytest -q tests/test_metrics.py -k unreviewed 2>&1 | tail -3   (red, before the code)
FAILED tests/test_metrics.py::test_a_landing_with_unreviewed_paths_carries_them_to_totals[2]
FAILED tests/test_metrics.py::test_a_landing_with_unreviewed_paths_carries_them_to_totals[unknown]
2 failed, 111 deselected in 0.09s
exit: 1

$ uv run --group dev pytest -q tests/test_land.py -k "fix" 2>&1 | grep -E "^E  |passed|failed"   (red, before the code)
E       AttributeError: module 'factory_landing' has no attribute 'cmd_land_fix'
3 failed, 22 deselected in 2.44s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py 2>&1 | tail -3   (red, before the skill edit)
FAILED tests/test_skills.py::test_skills_read_host_specifics_from_config[sdlc-factory:land]
1 failed, 343 passed in 0.42s
exit: 1

$ git log --oneline -1
473bfe1 Close 097-landing-fixes
exit: 0
