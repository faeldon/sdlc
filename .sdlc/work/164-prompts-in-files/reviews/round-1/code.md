VERDICT: PASS

I read the diff and the tests. I ran none of them myself, and I took the gate's result from `build/round-1.gate.md`: `GATE: PASS`, with the full `check.sh` green.

## Notes
- Requirements walked:
  - R1: no prompt prose is left in `factory.py`, and the files are in `plugins/factory/prompts/`.
  - R2/R3: the recorded copies in `tests/prompts/` (45 files) were recorded from the unchanged script, then the golden test was run against the base branch's scripts. That run is in the builder's evidence (47 passed, 12 skipped).
  - R4–R9: each has a named test in `tests/test_prompts.py` (the R5 test is `test_a_prompt_file_that_doesnt_match_is_refused`, plus a missing-file test).
  - R10: the only existing test edited is `tests/test_factory.py:3492`. It swaps `factory.RECHECK` for `factory.prompt_part("spec", "recheck")`, which is the rename the spec allows.
  - R11: the README names `plugins/factory/prompts/`, says the files are read from the plugin alone, and explains `${round}` and `$$`.
- `landing.py` is untouched, so `[review] sensitive` is not triggered.
- Context: I found no context doc that now says something false. `AGENTS.md` and `docs/` mention `_task_prompt` and `_land_task` only in the retro scorecard's baseline stats, which stay true.
- Done well: the golden copies are checked against the old script, and the validation checks parts, placeholders and stray `$` before any session starts. The README addition is short and accurate.
- The f-strings left in `factory.py` around line 1066 are suggestions to the person, not prompts sent to an agent, so they are correctly left in code.
- Tests and commands run: none. The gate record and the builder's evidence are what I relied on.
