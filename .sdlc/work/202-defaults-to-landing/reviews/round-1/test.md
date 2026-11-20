VERDICT: PASS

No CHANGE-level gaps. Each requirement has a test that would fail without it, and the gate passed. I only read test bodies and the gate record. I ran no tests.

## Notes

**Requirement to test map**
- R1: `tests/test_skills.py::test_the_approver_doc_offers_confirm` and the golden prompt `tests/prompts/approve-defaults.txt`.
- R2: `test_a_confirm_line_leaves_the_default_open` and `test_a_confirm_and_an_escalated_line_are_named_twice`. The first asserts D2 stays `- [ ]` and in `assumed` while D1 is still ticked.
- R3: `test_ready_with_an_uncarried_default_is_mended` runs the four parametrized cases (unlined, escalated, sensitive, closes). It asserts `stop`, `mend` and `["approver"]`, and that the problem names the id and the reason.
  - `test_a_confirmed_default_on_a_plain_change_is_done` is the positive control.
  - `test_a_second_uncarried_ready_is_a_rerun` checks that the mend prompt names the id and that a second READY is a rerun.
- R4: `tests/prompts/approve-defaults-sensitive.txt` and `approve-defaults-closes.txt`. `tests/test_prompts.py` and `mend-confirm.txt` also changed, which I take as the wiring.
- R5: `test_confirm_on_an_escalate_still_needs_deciding` asserts `confirm 1 default` and the `decide` step.
- R6: `test_ready_with_assumed_defaults_is_ready` asserts needs are empty, the column is `ready`, and there is no decide step. It also checks the board page still says "default(s) assumed".
- R7: `test_carried_defaults_keep_the_gate_the_persons` asserts the signal, `clear` false, the question clause, and the `--by auto` refusal. It also asserts no `Sdlc-Landed: by=auto` trailer is written.
- R8: `test_the_landing_shows_each_assumed_default_with_its_default` asserts exact entries, including the null `default` and `reason` for D2, and the exact `shown` text.
- R9: `test_the_landing_yes_confirms_carried_defaults` compares the whole ledger text. That proves no other line changes, the blocking one included.
- R10: `test_decide_answers_a_ready_changes_carried_defaults`, parametrized over kept and changed answers. It checks `confirm` is set and `escalated` is null.
- R11: `test_ship_shows_carried_defaults`.
- R12: `test_no_doc_says_any_default_escalates`.

**The run:** the gate record (`build/round-1.gate.md`) reads `GATE: PASS`, exit 0, with `3561 passed, 29 skipped in 208.30s`.

**Checks:** there is no `checks.md` in the change folder, so there is nothing to judge there.

- NIT: tests/test_factory_decisions.py:523: the "closes" case writes `closes: [12]` by string-replacing `idea:` in `intent.md`. If the fixture's frontmatter changes, the case could pass without exercising the `closes:` rule, though the assertion on `closes: [12]` in the problem text would still catch that. {tests S low}
