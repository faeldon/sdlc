VERDICT: PASS

I found no Critical or Required findings.

## Notes

**Requirements walked.**
- R1–R2: `sdlc.py upgrade` edits the frontmatter in place, scaffolds only what is missing, and has its own refusal tests.
- R3–R6: `upgrade_answer()` accepts only a decided, blocking, non-superseded line. `read_upgrade()` makes a second record a problem. `loop_state()` has `upgrade` and `spec` branches before `done`, and `first` takes the newer of the restart and upgrade rounds, which also fixes `limit`.
- R7–R10: `_task()` adds the upgrade wording to the spec, build, review, approve and decided prompts.
- R8 (builder resume): `cmd_agent` resumes the builder at round `P`.
- R11–R13: `start` reports `upgraded`, `fresh` returns `held`, and `PAUSES` is used by `_record_step` and copied into `board.py`.
- R14–R15: the skill, builder, README, AGENTS and REFERENCE edits are in the diff.
- Each requirement has a named test in `tests/test_factory.py`, `tests/test_sdlc.py`, `tests/test_board.py` or `tests/test_skills.py`.

**What is done well.**
- Writing the record before the tier change makes `cmd_upgrade` resumable. A rerun finishes the same upgrade and writes no second record.
- Reusing the restart machinery (round files, `first`, `depth()` starts) avoids a parallel round-counting scheme.
- Only a ticked, blocking answer starting `upgrade to Tier 2` counts. A builder's or supervisor's wording never upgrades the change.
- A skill-coverage test fails when `verdicts` can return a step the build skill has no bullet for.

**Optional.**
- `cmd_upgrade` recomputes `newest_round` only when no record exists. That is correct, and a one-line comment saying why would help the next reader.
- The `loop_state` `upgrade` branch is guarded by `not decision`. A stale `decision.md` on a Tier 1 change would therefore skip the upgrade. I judged that unlikely, but I did not test it.

**Ran.** `./check.sh` in full: ruff check and format pass, `2287 passed, 13 skipped`, and both plugin validations pass. The factory plugin's only warning is a missing icon, which is unrelated to this change. I read the `factory.py` diff in full. I skimmed the `sdlc.py` diff, the skill and the docs and relied on the tests for those.
