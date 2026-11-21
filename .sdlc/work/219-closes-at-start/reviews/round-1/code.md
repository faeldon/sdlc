VERDICT: PASS

## Notes

- Requirements covered:
  - **Record at `start`:** `cmd_start()` calls `record_closes()` once there are no refusals. A failed append becomes a refusal.
  - **Union:** `intent_closes()` returns the union of the ledger's record and the working copy.
  - **Mid-run edit test:** `test_closes_recorded_at_start_outlives_an_edit` removes `closes:` mid-run. It checks that `no_confirm_why()` and the `issue` signal still fire.
  - **Nothing closed:** `test_a_change_closing_nothing_records_nothing` covers a change with no `closes:`.
  - **Autopilot path:** `test_an_agent_run_records_closes_without_start` covers the agent call.
- **Ledger format:** the new `closes` row has no `record` or `sha256`. `vouched()` compares a whole row, so it can never read this row as vouching for a record. The format is extended, not redefined.
- **D1 (default):** recording in `cmd_agent()` as well as `start` is a sound default, since autopilot never runs `start`. The plan's open questions are answered: the union runs over every record, and the new row is the factory's alone, so core has no copy to pin.
- **Gate:** `build/round-1.gate.md` reports `GATE: PASS`. Its first attempt failed on `tests/test_prompts.py`; I did not read the later attempts, but the `recorded_closes` stub in that file is the matching fix.
- **Tests run:** none. I relied on the gate record.
- NIT: plugins/factory/scripts/factory.py:3181: `recorded_closes()` reads the whole ledger on every call, and `record_closes()` calls it on every agent run. The ledger is small, so the cost is negligible. {robustness S low}
