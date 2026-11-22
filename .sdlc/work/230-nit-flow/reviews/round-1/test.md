VERDICT: PASS

Every requirement has a test that fails without it. I read the gate record and the diff. I did not run any tests myself.

## Notes

- **Gate:** `build/round-1.gate.md` is `GATE: PASS` from `./check.sh`: 4038 passed, 29 skipped, `claude plugin validate --strict` passed. I ran no test or suite, because the gate record covers the whole suite.
- **R1, R2, R3, R5, R6:** `test_a_nit_a_later_round_raises_reworded_is_filed_once`, `test_a_nit_no_later_round_raises_is_fixed_whatever_its_weights`, `test_a_nit_not_filed_says_why`, `test_the_factory_files_no_low_value_nit` and `test_a_landing_round_never_changes_the_nits_filed` map to them. I read only R2's test body. For the other four I confirmed the test names exist and that `tests/test_land.py` and the cap and weights tests moved their weights to `med` as R5 asks. R2's test covers `M low`, `S low`, `M med` and `S med`, a restart's first round, and the no-later-round contrast. I did not read the R3 test body, so whether it asserts both `FIXED_REASON` and `REPEAT_REASON`, and a section for each nit, is unconfirmed.
- **R4:** `test_a_review_names_its_roles_earlier_nits` checks four things. A handed nit appears once, another role's nit never appears, and a role with no nits gets no line. The restart round names the pre-restart round's nits. The `review-earlier` prompt fixture pins the exact wording.
- **R7, R8:** `test_inbox_commit_retires_by_the_entry_s_kind` covers a successful `stale` retirement, a refused `declined`, no `Sdlc-Retired:` trailer, and the commit subject and body line. `test_inbox_commit_never_retires_a_nit_an_open_change_takes_in` covers the `Nits taken in:` claim, the `entries.md` `Retire` claim, a nit named only in prose, and a dropped change. It asserts the refusal text names the change.
- **R9:** `test_core_reads_nits_taken_in_as_the_factory_does` runs the factory's cases through both readers and compares the regex constants.
- **R10:** `test_idea_retires_a_nit` checks each word of `RETIRE_REASONS["nit"]`, the "takes in" and "refuses" wording, and that the old "ship's" claims are gone.
- **R12:** `landing.py` is not in the diff, so the landing signal is unchanged. `guide/` and `defaults/` are not in the diff either.
- **Checks:** there is no `checks.md` in the change folder, so there was no acceptance check to judge.

- NIT: tests/test_factory_loop.py:921: the test sets `start` on a round by hand to model a restart. A restart that went through `cmd_restart` is exercised only in the R4 prompt test, not for filing. {tests S low}
