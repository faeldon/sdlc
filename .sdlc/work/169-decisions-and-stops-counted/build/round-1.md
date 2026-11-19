I've built all 16 requirements and left them uncommitted for ship. The full gate passes (3094 passed, 28 skipped). A read-only `retro` on this repo's own history now shows 13 factory changes and 1 built by hand, with every figure carrying its `n`, and the tree unchanged afterwards. I raised no decisions.

## Slices built

1. **Counting a run's records (R1–R4, R10).**
   - `factory_records.autonomy_counts(show, listing)` returns None for a change built by hand.
   - For a factory run it counts:
     - escalations, in the current decision and each archived `decision-<n>.md`;
     - each ledger line, by its mark;
     - build mends apart from landing mends.
   - Ledger answers are compared exactly, never by prefix, because `KEPT_ANSWER` is a prefix of `CONFIRMED`.
   - New copies under `factory.py`'s names: `ARCHIVE_RE`, `MENDED`, `KEPT_ANSWER`, `CONFIRMED`, `SUPERSEDED`. Also core's own `LOOK_SEEN`. All are added to `RECORD_NAMES`.
2. **`autonomy` in retro's JSON (R5–R9, R16).**
   - `retro.py` gains `_records_at` (reads a closed change's folder at its own commit through `sdlc._git`) and `_autonomy`.
   - The JSON gains `factory`, `by_hand`, `escalations`, `asked`, `kept_default`, `overturned`, `auto_landed`, `spurious_stops` and `looks`.
   - `closed_changes()` keeps `rec["landed"]` from the change commit's trailers it already parses, so this costs no extra git call.
   - A decision file with no readable answer becomes a problem naming the change and the file.
   - `UNMEASURED` gains its two entries.
3. **After-gate stops name their skill (R11, R12).**
   - Each `after_gate` stop now records the skill whose WAIT it followed, written as `Sdlc-AfterGate: <skill> stops=<n>` and read back by `parse_trailers()`.
   - Retro's `metrics.extra` gains `after_gate_by` and `after_gate_unnamed`.
   - Existing trailer lines are unchanged.
4. **Status nits (R13, R14).**
   - `held_by_rebase()` now lists the change worktrees once and passes them to `rebasing_branches(root, trees=None)`.
   - `_by_state()`'s fallback now calls `column()`.
5. **Docs (R15).**
   - `docs/REFERENCE.md`: the *Retrospectives* section describes `autonomy`; the *Metrics* section names `Sdlc-AfterGate`.
   - The `metrics.py` and `factory_records.py` docstrings, and the map sentence in `AGENTS.md`, are updated.

## Tests added
- R1–R4: `test_autonomy_counts_are_none_for_a_change_built_by_hand`, `…_every_escalation_current_and_archived`, `…_read_each_ledger_answer_by_its_mark`, `…_tell_a_landing_mend_from_a_build_mend`
- R5, R16: `test_retro_autonomy_says_a_decision_it_cannot_read`
- R6: `test_retro_autonomy_leaves_hand_built_changes_out`
- R7, R16: `test_retro_autonomy_counts_auto_landed_from_the_change_commit` (one fixture has `by=auto` only on the `Close` commit, and must count as `shipped`)
- R8: `test_retro_autonomy_rates_kept_defaults_without_the_landings_yes`
- R9: `test_retro_says_what_autonomy_cannot_count`
- R10: `test_look_seen_is_the_decide_skills_answer`, plus the existing through-`sdlc` and "defined only in `factory_records.py`" tests, which now also cover `retro.py`
- R11: `test_an_after_gate_stop_names_the_skill_whose_gate_it_followed`
- R12: `test_retro_names_the_skill_an_after_gate_stop_followed`
- R13: `test_held_by_rebase_walks_the_change_trees_once`
- R14: `test_by_state_places_a_record_without_a_column_as_column_does`, over every stage × factory/manual

I watched each fail for the expected reason before writing its code: a missing attribute or key, the R13 test seeing 2 calls, and 5 of the 16 R14 cases misplaced.

## Changes to `plan.md`
I wrote it before any code. Since then I added an *As built* section:
- **`asked.blocking`** counts only blocking decisions the person answered. That matches `default` (kept or changed) and `look` (seen or checked).
- **`retro.py` checks:** the "defined only in `factory_records.py`" check now covers `retro.py` as well.
- **R8 test:** an extra test runs R3's ledger through `retro()`.

## `notes.md`
Nothing left there.

My first full gate run stopped at `ruff format --check` on the new R12 test. I reformatted the file, and the second run is the green one below.

- UNTESTABLE: none

## Evidence

$ uv run --group dev pytest -q -n 4 tests/test_retro.py tests/test_metrics.py tests/test_modules.py -k "autonomy or after_gate or cannot_count or records_through_sdlc or look_seen or shared_name or record_readers or named_outside"
16 passed in 63.28s (0:01:03)
exit: 0

$ uv run --group dev pytest -q tests/test_sdlc.py -k "held_by_rebase_walks or by_state_places"
17 passed, 269 deselected in 0.47s
exit: 0

$ uv run --group dev pytest -q -n 4 tests/test_sdlc.py tests/test_board.py
569 passed, 28 skipped in 72.97s (0:01:12)
exit: 0

$ uv run --group dev ruff check . && uv run --group dev ruff format --check .
All checks passed!
307 files already formatted
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 169
All checks passed!
3094 passed, 28 skipped in 200.96s (0:03:20)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro   (autonomy and metrics.extra extracted; git status --porcelain compared before and after)
"factory": 13, "by_hand": 1, "escalations": {"total": 3, "changes": 3, "per_change": 0.23, "n": 13}, … "overturned": {"count": null, "n": 0, "unmeasured": "an approver's settled call the person overturned"} …
{} 2 {'count': 2, 'changes': 1}
unchanged
exit: 0
