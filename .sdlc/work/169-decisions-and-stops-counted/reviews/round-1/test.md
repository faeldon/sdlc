VERDICT: PASS

Every requirement from R1 to R16 has a test that would fail without it. I found no test that can't fail. I didn't re-run the suite or any named test; I relied on the gate's record.

## Notes

**Requirement to test map**
- R1 → `test_autonomy_counts_are_none_for_a_change_built_by_hand`. It checks both `None` for a hand change and a dict with zero escalations for a factory one.
- R2 → `test_autonomy_counts_every_escalation_current_and_archived`. It has two archived escalations plus a current READY, and an escalation under `reviews/round-1/` that must not count. It also checks the alone case.
- R3 → `test_autonomy_counts_read_each_ledger_answer_by_its_mark`. It pins `CONFIRMED.startswith(KEPT_ANSWER)` and has one line of each mark.
- R4 → `test_autonomy_counts_tell_a_landing_mend_from_a_build_mend`. Its garbled lines include an empty line, `builder` alone, `reviewer round-2` and `verifier land-x`.
- R5 → `test_retro_autonomy_says_a_decision_it_cannot_read`. It checks `n` is 1, not 2, and that the problem names both the change and `decision-1.md`.
- R6 → `test_retro_autonomy_leaves_hand_built_changes_out`.
- R7 → `test_retro_autonomy_counts_auto_landed_from_the_change_commit`. The `Close`-commit-only trailer counts as `shipped`. R16 is covered by the `_state()` comparison.
- R8 → `test_retro_autonomy_rates_kept_defaults_without_the_landings_yes`.
- R9 → `test_retro_says_what_autonomy_cannot_count`.
- R10 → the extended `test_modules.py` tests plus the new `test_look_seen_is_the_decide_skills_answer`.
- R11 → `test_an_after_gate_stop_names_the_skill_whose_gate_it_followed`. It checks the round trip and that the `Sdlc-Extra` lines are unchanged. It also checks no `Sdlc-AfterGate` line is written when there are no stops.
- R12 → `test_retro_names_the_skill_an_after_gate_stop_followed`. The pre-`Sdlc-AfterGate` commit's 3 stops land in `after_gate_unnamed` and under no skill.
- R13 → `test_held_by_rebase_walks_the_change_trees_once`. It asserts one call, and that `rebasing_branches(root)` alone still walks the trees.
- R14 → `test_by_state_places_a_record_without_a_column_as_column_does`. It is parametrized over every stage in `STAGES` and both modes.
- R15 is docs: `AGENTS.md` and `docs/REFERENCE.md` are in the diff, as are `metrics.py` and `factory_records.py`. I didn't check their wording against the spec's list.

**Gate:** `build/round-1.gate.md` is PASS, `./check.sh`, exit 0, 3094 passed, 28 skipped, 661.83s.

**Checks:** there is no `checks.md`, and none is needed.

- NIT: tests/test_retro.py:2606: R8's rate test lets one ledger give `kept=1, changed=1`, so `kept/(kept+changed)` and `kept/total_defaults` can't be told apart by the 0.5 rate alone. A test with `confirmed` or `settled` lines that outnumber the rest would fail if the denominator changed. {tests S low}
