VERDICT: PASS

## Notes

- NIT: docs/REFERENCE.md:575: the edited line is now about 110 characters, while its neighbours wrap near 100. Rewrap the paragraph. {style S low}
- NIT: scripts/factory_records.py:300: `specifying()` has a lot of branching and repeats the read-text-if-file pattern three times. A small helper would shorten it. {refactor S low}

**Done well:**
- `stage:` is never touched, and `column()` stays the single rule that both the board and `status` call.
- Core's records stay inside `factory_records.py`, and the new names are pinned in `RECORD_NAMES`.
- `SPEC_SESSIONS` is pinned to the factory's own `agent_name()` and `TASK_ROLE`.
- The test covers all five cases (STEP spec, waiting draft, running session, returned session with its draft gone, neither) on both the board and `status`, and checks the `stage: plan` line is unchanged.
- The ledger records D1 and D2, the two deviations from the intent's Approach. D2 is a sound default, and it makes a spec-writer that crashes before reporting cost stay under Designing, which D2 states.

**Ran:** I read `build/round-1.gate.md`. The gate is `PASS`. I ran no tests myself.
