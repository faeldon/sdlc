VERDICT: PASS

Every R1–R17 test the spec names exists, and none passes without its code. I spot-read two of them, the settle-refusal cases and the decide WAIT ordering.

## Notes

- Coverage by requirement:
  - R1, R3: `test_a_defaults_alternatives_reach_the_ledger_under_its_line` and `test_options_fill_a_bare_line_once` (byte-identical rerun).
  - R2: `test_a_ledger_without_alternatives_reads_as_before` in `tests/test_factory.py`, plus `test_a_ledger_with_alternatives_is_not_garbled` in both `tests/test_sdlc.py` and `tests/test_board.py`.
  - R4: `test_agents_give_a_defaults_alternatives`.
  - R5: `test_the_approver_is_asked_to_weigh_each_open_default`.
  - R6: `test_the_approver_settles_one_default_and_escalates_another`, and `test_a_settle_that_cant_apply_marks_nothing`, parametrized over blocking, decided, superseded, unknown and twice. The "twice" case is extra to the spec.
  - R7: `test_a_settled_default_is_not_the_persons_word`.
  - R8, R9: `test_the_landing_shows_settled_defaults_apart_and_never_confirms_them`, `test_a_superseded_default_is_neither_assumed_nor_a_signal_nor_a_decision` and `test_a_settled_default_keeps_the_batch_from_passing_itself`.
  - R10: `test_an_escalation_with_only_settled_defaults_is_not_answered` in both `tests/test_sdlc.py` and `tests/test_board.py`.
  - R11: `test_a_settled_default_is_counted_apart`.
  - R12: `test_ship_shows_settled_defaults_apart`.
  - R13, R14: the four `test_ask_*` tests.
  - R15: `test_decide_writes_answers_only_after_its_wait` and `test_decide_never_takes_words_on_a_command_line`.
- `decide` has no `checks.md`, and none is needed.
- The test command was `uv run --group dev pytest -q -n auto`. It ran 2448 passed and 13 skipped, with no failures.
