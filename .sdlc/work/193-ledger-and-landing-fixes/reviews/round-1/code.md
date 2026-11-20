VERDICT: PASS

Every requirement in the intent has code and a test that would fail without it. The gate record `build/round-1.gate.md` is green.

- **Continued questions:** `question_lines()` folds a decision's indented continuation into its ledger line, blank lines included. The `- OPTION:` and `- WHY:` run is then read from where the continuation ends. `test_a_question_in_sub_bullets_keeps_every_line_and_its_options` covers 187's D3 shape.
- **Ledgers already written:** `cmd_decisions` also matches a raise by its first line alone, so an old ledger isn't filed again and its bare line gets its options once. The new test covers this, including a rerun that changes nothing.
- **Raised twice:** a raise with the same source, kind, options and why as a filed one lands once. `test_a_decision_reraised_with_the_same_alternatives_lands_once` checks both the merge and the cases that must stay separate. D1's trade-off is recorded in `decisions.md` as an open default: two different questions with identical alternatives would be filed once.
- **grep prefixes:** `len(name) >= 5` is the three characters after `--` that the plan names. So `--der` is refused, while `--de` and `--directories=skip` pass. The `=value` forms are refused too, and the refusal only gets stricter.
- **Docs and wording:** the land description, the `read_only_command` docstring and the `_train_begin` comment are done. AGENTS.md needs no change, as the plan says.

## Notes
- Well done: the plan's rule that the match for a resumed agent's reworded raise sits in `cmd_decisions`, not in `raised_decisions()`. The earlier reply is rewritten on resume, so only the ledger still holds it.
- Well done: the tests pin the boundary cases (`--de` passes, `--der` is refused).
- NIT: plugins/factory/scripts/factory.py:2018: `by_alts` is built from every ledger entry with options. The match relies on options and why being identical, so a very short shared option list could merge two real decisions. D1 already accepts this trade-off. {robustness S low}
- I ran no tests. I read the gate record for the result.
