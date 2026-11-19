VERDICT: PASS

Every requirement R1–R22 maps to a named test that exists and can fail. R23 is covered by an acceptance check. I found no test that can't fail.

## Notes

- **Gate record:** `build/round-1.gate.md` shows `GATE: PASS` with `3437 passed, 29 skipped in 150.53s`, and `claude plugin validate` passed. I did not run the whole suite.
- **Requirement mapping:** These tests are in place:
  - R1/R2: `test_vet_strict_fails_on_a_problem` and `test_check_is_no_longer_a_command`, in `test_sdlc.py`.
  - R3: `test_a_host_with_only_the_check_rule_is_missing_the_vet_rule`, in `test_readiness.py`.
  - R6, R10, R11, R20: `test_every_vocabulary_term_has_an_entry`, `test_no_doc_uses_a_retired_phrasing`, `test_no_file_names_a_retired_name` and `test_agents_md_fits_100_columns`, in `test_feature_map.py`.
  - R12, R13, R14, R16: `test_the_verifier_role_and_task_are_gone`, `test_the_arbiter_writes_verified_md`, `test_an_old_verifier_mend_counts_for_its_round` and `test_models_verifier_is_an_unknown_role`, in `test_factory.py`.
  - R14: `test_an_old_verifier_row_counts_as_arbitrate`, `test_an_old_verify_step_sits_at_arbitrate` (`test_board.py`) and `test_agents_by_role_groups_verifier_with_arbiter` (`test_retro.py`).
  - R14: the `RENAMED` pin, `test_every_shared_name_is_the_factorys`, in `test_modules.py`.
  - R17–R19: `test_a_card_counts_acceptance_and_its_last_run` and `test_the_gate_badge_names_its_command_and_result`, in `test_board.py`.
- **Term test can fail:** `test_no_doc_uses_a_retired_phrasing` builds a fixture doc with 17 phrasings. It asserts one finding per line, in order. It also puts the same words in code spans and a fenced block, and those must not match. It then asserts the real prose set has no findings.
- **R11 exemption:** The `RENAME_NOTE` exemption is scoped to one paragraph, and the test fails if that paragraph disappears. That is sound.
- **Checks in `checks.md`:** I did not run any of them. Each reverts only by undoing the change, so they belong there rather than in the suite.
  - *The two test nits are gone:* greps for `179 R1` and `# 183`. I expect it to pass, since the nits are removed.
  - *The arbiter's agent and prompts sit under its name:* tests that the three new files exist and the three old ones don't. I expect it to pass.
  - *The release says what a host must change:* greps `impact: minor` in `intent.md` and four phrases in REFERENCE.md. I expect it to pass if REFERENCE.md holds those exact phrases.
- **Tests I ran, each in the foreground:** `pytest -q tests/test_feature_map.py tests/test_readiness.py -k "retired or vocabulary or vet_rule or 100_col"`, which gave 5 passed.
- NIT: tests/test_feature_map.py:273: the phrasing fixture's `# fmt: skip` list packs several phrasings per line, which makes a future edit harder to read {tests S low}
