VERDICT: PASS

No requirement lacks a test, and no test I read is unable to fail. The gate's record is green on attempt 2.

## Notes

- **Gate:** `build/round-1.gate.md`. Attempt 1 failed with "12 failed, 3938 passed, 29 skipped". The failures were `test_prompts.py::test_every_prompt_matches_its_recorded_copy[...]`, which hit an unstubbed `rev-parse --git-common-dir` call. The builder's one-line stub of `recorded_closes` in `tests/test_prompts.py` fixed it. Attempt 2 shows "3950 passed, 29 skipped". I ran no tests myself.
- **Requirement map:**
  - Outcome 1 (`start` records `closes:` once): `test_closes_recorded_at_start_outlives_an_edit` runs `start` twice and asserts exactly one row.
  - Outcome 2 (union, never a drop): the same test removes `closes:`, then sets `[12, 15]`, then `[15]`, and checks `intent_closes`.
  - Outcome 3 (`no_confirm_why` and the `issue` signal): the same test asserts both after the edit. It passes `pre={}`, so it fails without the `land_signals` change.
  - Constraint (no `closes:` writes nothing): `test_a_change_closing_nothing_records_nothing`.
  - Autopilot path: `test_an_agent_run_records_closes_without_start`.
- **No `checks.md`:** the change has none, and none is needed.
- **Ledger row shape:** the new row has no `record` or `sha256`, so it can't vouch for a record.
- **NIT:** `tests/test_factory_decisions.py`: the OSError path (`start` refusing when the ledger can't be appended to, and `cmd_agent` returning its refusal) has no test. {tests S low}
- **NIT:** `tests/test_factory_decisions.py`: the agent test doesn't check that a second agent run adds no second row. `start` already covers "once" through the shared `record_closes`. {tests S low}
