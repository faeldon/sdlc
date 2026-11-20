# Decisions

- [x] D1 (builder round 1, default): Keep a draft waiting for the yes under Designing, not Needs you (the intent's open question). Going ahead with Designing unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: Designing — matches the intent's Outcome and the person's words; the waiting yes shows only as the change sitting there
  - OPTION: Needs you for a waiting draft, Designing only while the spec-writer runs — puts the owed yes in front of the person; differs from the Outcome as written
  - WHY: the intent's Outcome and its test line both say a waiting draft lands in Designing
- [x] D2 (builder round 1, default): Count a spec-writer as running when its newest session has no row in `runs/costs.jsonl`, since a first draft writes no `runs/step.md`. Going ahead with this unless told otherwise. → settled by the approver: `plan.md`'s *What the code says* shows that a first spec draft runs `factory.py agent --task spec` and writes no `runs/step.md`. The newest `runs/spec-writer.sessions` id with no `runs/costs.jsonl` row is the only record that meets the Outcome's "while its spec-writer runs" without touching the factory, which is outside *Affected*. `specifying()` at `scripts/factory_records.py:300` does this, `test_a_plan_change_being_specified_is_designing` covers a running session and a returned one, and the code reviewer called it a sound default. The one known cost: a session that crashes leaves the card under Designing. That only affects the display, and the ledger says so.
  - OPTION: a session with no cost row — catches the first draft; a session that dies without reporting costs stays under Designing until its folder is cleared
  - OPTION: only `runs/step.md` and `runs/spec-draft.md`, as the Approach says — simpler; a first draft shows Planned while it runs, which misses the Outcome
  - OPTION: have `factory.py agent --task spec` write a step record — one signal for both cases; changes the factory and `runs/step.md`'s meaning, outside the change's Affected list
  - WHY: the Outcome asks for Designing "while its spec-writer runs", and this is the only record a first draft leaves without touching the factory
