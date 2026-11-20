# 200 — Plan

> Tier 1, written because the Approach reaches five files. How the intent's Approach is built:
> the files, the order, the tests, and what a revert wouldn't undo.

## Files to change

- `tests/test_train.py`: the seven slow train tests. Profiling shows each one's setup (`_three()`,
  `_ready()`) takes under a second of its 15–40: the time is the train's own steps (about 1,500 git
  calls for a driven train of three, about 12 step subprocesses for `train --run`). So sharing a
  fixture saves nothing; walking one train through several checks, and dropping a train whose
  checks another already makes, does:
  - `test_every_ejection_names_its_cause` (three trains): each cause is already proved by a
    `train --run` test reading the same reading: `gate` by
    `test_train_run_ejects_a_gate_fault_and_lands_the_rest` (the loop ejects only a `gate` cause),
    `review` by the kept-change test (the stop's `cause`, `--eject`'s `cause`, the exit's
    `ejected`), `refusal` by `test_train_run_stops_at_a_refusal`. Removed, once a mutation of
    each `ejecting(..., cause)` call shows a remaining test failing.
  - `test_train_run_resumes_after_a_kept_change` merged into
    `test_train_run_stops_at_a_kept_change`: one `_kept_at_two()` train, stopped, then ejected and
    resumed.
  - `test_train_run_lands_a_batch_of_three` merged into `test_a_killed_train_run_resumes`: the
    resumed loop's exit is checked as the batch's was (`landed`, `ejected`, `gates`, the agents).
    Both need uv and neither is `portable`.
  - `test_a_train_stops_past_land_moves` merged into
    `test_a_move_mid_train_re_stacks_the_rest_and_counts_once`, under `[land] moves = 1`: the
    first move is followed (B re-stacked, gated, reviewed again and closed, counted once), the
    second, before C closes, stops the train with C back at its pre-train commit.
  - `test_a_train_fix_already_made_goes_on_to_the_gate`: its driven half dropped; the `train
    --run` half checks the order (fix, then the tip's gate, then the review) from the loop's
    progress lines, beside the full-depth review it already checks.
- `tests/test_land.py`: `test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone`
  lands two changes, not three: one carrying the checks and the note, one the irreversible path.
- `scripts/indicators.py`: `drifted_tests()` takes a `read(path)` of a file's text. A test's code
  is the code its last change touched that the test loads (`loads()`, new). That is a code file
  it names in a string or as a path (`_names()`: never in backticks, never a bare word with no
  suffix, and matching the path's trailing segments), or one whose stem an import line names.
  It is followed through the test helpers an import line names, never one that is only
  mentioned. A data file (`DATA_SUFFIXES`: a golden, a fixture, a prompt) loads nothing and is
  no one's code, so it never drifts. A change too large to pair still counts as a test's last
  change, giving it no code. Run on this repo, the first, looser rule matched prose mentions and
  `branch` files, and two tests were dated past their real last change, 187: hence the stricter
  rules.
- `scripts/retro.py`: `_tests()` passes a reader of each file at the base branch (`git show`,
  UTF-8 with `errors="replace"`, None when it fails).
- `tests/test_indicators.py`, `tests/test_retro.py`: the existing drift tests given texts; new ones.
- `docs/REFERENCE.md` (*Retrospectives*), `skills/retro/SKILL.md`: what `drifted` reads.

Reused: `indicators.classify()`, `_files()`, `PAIR_FILES_MAX`, `DRIFT_LEAST`; `sdlc._git`'s shape
for the reader.

## Work order

1. **Drift reads what a test loads.** `indicators.loads()` and the narrowed `drifted_tests()`,
   test first in `test_indicators.py`; then `retro._tests()`'s reader, test first in
   `test_retro.py`; then the docs. Run the new drift on this repo and look at each of the nine
   old ones; `notes.md` says what each became.
2. **The slow tests.** Each merge above, one at a time, its tests run by name; then each removed
   test's causes mutated to show a remaining test fails; then the eight (and the tests that took
   them in) timed against the baseline.

## Tests

- Intent outcome 2 (drift reads loads): `test_a_test_drifts_only_with_the_code_it_loads`,
  `test_a_golden_never_drifts`, `test_loads_follows_a_helper_the_test_imports`,
  `test_loads_reads_names_and_imports` (one case per way of naming and not naming),
  `test_a_test_touched_by_a_change_too_large_to_pair_starts_again` (indicators);
  `test_drift_reads_the_test_at_the_base_branch` (retro), and the existing drift tests, given
  texts.
- Intent outcome 1 (the eight under half): the timing, recorded in the report's evidence; each
  merged test still fails without its code, shown by the mutations in the report.

## Rollback

Nothing a `git revert` wouldn't undo: tests, a pure function, and docs. No data written.
