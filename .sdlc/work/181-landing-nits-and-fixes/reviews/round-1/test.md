VERDICT: PASS

Every requirement R1–R10 has a test that fails without it, and the gate's record is green.

## Notes
- **Gate record** (`build/round-1.gate.md`): `GATE: PASS`. The first attempt failed on 3 tests in `tests/test_adoption.py`, each with a DNS lookup error from `uv` (no network). The second attempt passed: `3163 passed, 29 skipped`, with `ruff` and `claude plugin validate --strict` clean.
- **Named run:** I ran the new and extended tests in the foreground and `7 passed, 141 deselected`.
  - Command: `pytest tests/test_land.py -k "nit_named_but_not or nits_taken_in_line or already_made or fix_commit_needs"`, plus `tests/test_train.py::test_a_train_fix_already_made_goes_on_to_the_gate` and `tests/test_prompts.py -k land_fix_prompt`.
- **Requirement to test:**
  - R1: `test_a_nit_named_but_not_taken_in_stays` checks `retired_nits`, the `Retire` lines and the register after close.
  - R2: `test_the_nits_taken_in_line_is_read_in_its_forms` covers the plain, list, bold and case forms, a continuation, a blank line ending it, whole-id matching, a marker under `## Problem`, and a mid-line "marker".
  - R3: the existing nit tests were migrated to the marker line.
  - R4: `test_every_place_that_takes_a_nit_in_names_the_marker`.
  - R5: `test_a_fix_already_made_goes_on_without_a_commit` asserts `HEAD` is unmoved, `already_made` is true and the stored fix is `done`.
  - R6: the extended `test_a_fix_commit_needs_an_ask` covers a missing report, no claim, disagreeing `FIX:` lines, no `## Evidence`, and no `exit:` line. Each case asserts `HEAD` is unchanged.
  - R7: `already_made` is asserted false in `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth`.
  - R8: `test_a_train_fix_already_made_goes_on_to_the_gate` runs both the driver steps and `train --run`. It checks that a gate comes before the review, that every reviewer runs, that no stop appears and that the file is not edited.
  - R9: `test_a_fix_already_made_is_still_a_signal` covers the signal, `fixed: true` and the `land --close` refusal on a `by=auto` commit.
  - R10: `test_the_land_fix_prompt_tells_a_fix_already_made`, plus the re-recorded `tests/prompts/land-fix.txt`.
- **Plan departure:** the plan widens `FIX_RE` to any `FIX:` answer, so that disagreeing lines can exist and R6 is testable. This is sound, and `landing.py` compares the answer to `FIX_MADE`.
- **`checks.md`:** the change has none, and no requirement needs one.
- NIT: tests/test_land.py: the `_already_made` helper and `test_a_fix_commit_needs_an_ask` write `MADE` and `ALREADY` module constants in the middle of the file, and `tests/test_train.py` defines a second `MADE`; hoist them or rename them to avoid confusion {tests S low}
