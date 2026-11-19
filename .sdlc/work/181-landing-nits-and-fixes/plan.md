---
id: 181
slug: landing-nits-and-fixes
kind: plan
created: 2026-11-19
updated: 2026-11-19
---

# 181 — A landing retires only the nits it takes in, and goes on past a fix already made · plan

> Written by the builder after reading `named_nits()`, `cmd_land_fix()`, `land_signals()`, the
> train driver and the tests that pin them.

## Files to change

- `plugins/factory/scripts/factory.py`: `TAKEN_RE` and `taken_lines()` beside `NIT_SECTIONS`;
  `named_nits()` searches only the marker lines (reuses `_section()`, `NIT_RE`, `FENCE_RE`);
  `FIX_RE` and `FIX_MADE` beside `VERDICT_RE`. **Departs from the spec's design:** `FIX_RE`
  reads any `FIX: <answer>` line (`^FIX: (\S.*?)\s*$`), and only an answer of `ALREADY MADE`
  goes on. The design's regex matched only `ALREADY MADE`, so two `FIX:` lines could never
  disagree, and R6's "lines that disagree" refusal couldn't hold.
- `plugins/factory/scripts/landing.py`: `cmd_land_fix(commit=True)` with nothing fixed reads
  `build/land-<n>.md` through a new `_not_already_made()` (`factory.opening()`,
  `factory.read_evidence()`), then `_train_fix(done=True)`; `already_made` in both outputs.
- `plugins/factory/prompts/land-fix.md`: `## main` names `FIX: ALREADY MADE`.
- `tests/prompts/land-fix.txt` (the recorded copy): re-recorded (`SDLC_RECORD_PROMPTS=1`).
- `tests/test_land.py`: the five `Takes in nit …` lines become `Nits taken in: …`;
  `test_the_landings_nits_are_the_ones_sdlc_reads` puts its ids on a marker line; new
  `test_a_nit_named_but_not_taken_in_stays`, `test_the_nits_taken_in_line_is_read_in_its_forms`,
  `test_a_fix_already_made_goes_on_without_a_commit`, `test_a_fix_already_made_is_still_a_signal`;
  extended `test_a_fix_commit_needs_an_ask` and
  `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth`.
- `tests/test_train.py`: new `test_a_train_fix_already_made_goes_on_to_the_gate` (driver steps,
  then `train --run` with a stand-in builder that edits nothing).
- `tests/test_prompts.py`: an assertion on the built `land-fix` prompt.
- `tests/test_skills.py`: new `test_every_place_that_takes_a_nit_in_names_the_marker`.
- `skills/intent/SKILL.md`, `skills/intent/batch.md`, `skills/spec/SKILL.md`,
  `plugins/factory/skills/land/SKILL.md`, `plugins/factory/README.md`: prose names the
  `Nits taken in:` line; land skill and README say a fix already made goes on.

## Work order

1. **Nits by the marker** (R1–R3): red tests for R1/R2, then `taken_lines()`/`named_nits()`,
   then migrate the existing tests' prose to the marker, run the nit tests by name.
2. **The marker in the words** (R4): red skills test, then the five prose edits.
3. **A fix already made** (R5–R7, R9): red tests in `test_land.py`, then `FIX_RE` and the branch
   in `cmd_land_fix()`.
4. **The train** (R8): the train test, seen red against the old refusal put back for one run.
   The tip's gate runs under the tip's change, so the test asserts a gate comes after the fix
   and before change one's review.
5. **The prompt** (R10): red assertion, prompt edit, re-record the golden copy.

## Tests

- R1: `test_a_nit_named_but_not_taken_in_stays`.
- R2: `test_the_nits_taken_in_line_is_read_in_its_forms`.
- R3: `test_the_landings_nits_are_the_ones_sdlc_reads`, `test_a_landing_retires_the_nits_its_intent_names`,
  `test_a_landing_whose_commit_failed_commits_on_rerun` (and the other marker-migrated tests).
- R4: `test_every_place_that_takes_a_nit_in_names_the_marker`.
- R5: `test_a_fix_already_made_goes_on_without_a_commit`.
- R6: `test_a_fix_commit_needs_an_ask` (extended).
- R7: `test_a_fix_asked_at_landing_is_built_gated_and_reviewed_at_depth` (`already_made` false).
- R8: `test_a_train_fix_already_made_goes_on_to_the_gate`.
- R9: `test_a_fix_already_made_is_still_a_signal`.
- R10: `test_the_land_fix_prompt_tells_a_fix_already_made` in `tests/test_prompts.py`, and the
  recorded copy.

## Rollback

`git revert` undoes all of it: no data is written outside the repo, no template or config key
changes. A nit a landing under this change left open that the old code would have retired stays
in the register; a revert doesn't retire it either (retire by hand if wanted). An intent written
with a `Nits taken in:` line still retires under the old code, which matched any id.
