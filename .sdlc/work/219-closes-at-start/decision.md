DECISION: READY

**Why:** All three Outcome requirements and the "no `closes:`" constraint are built and tested, and every round-1 reviewer returned PASS. The gate's attempt 2 is green (3950 passed). The 12 `test_prompts.py` failures from attempt 1 were fixed with a one-line stub. The only departure from the Approach, recording in `agent` as well as `start`, is explained in the build report and endorsed by the code, security and behaviour reviews, because autopilot never runs `start`.

**Open items**
- NIT (code reviewer): `recorded_closes()` reads the whole ledger on every agent run. The cost is negligible.
- NIT (security reviewer): in `cmd_agent`, `_record_land()` runs before `record_closes()`. A failed append would leave a landing record for an agent that is then refused.
- NIT (test reviewer): there is no test for the OSError refusal path, and none checking that a second agent run adds no second row.

None of these needs a rebuild.

**Decisions to confirm**
- SETTLED: D1: The Outcome says what a change closes is fixed "before any agent runs", and plan.md and the builder's report show autopilot never runs `start`. Recording in `agent` as well is therefore the Approach's own intent, which the code and security rounds endorsed, and it adds no scope, policy, cost or interface.

**For the person at ship**
- Look first at `plugins/factory/scripts/factory.py`: `record_closes()`, `recorded_closes()`, `intent_closes()`, and the call in `cmd_agent` (see the `_record_land` ordering nit).
- Then `plugins/factory/scripts/landing.py: land_signals()`, which is a sensitive path.
- The records ledger format is extended, not redefined. The new row has no `record` or `sha256`, so neither `vouched()` nor core's `vouched_in()` can read it as vouching for a record. This is the "Contracts" item in the intent, and the person approved it there.
- Known Low gap: a shell command could truncate the ledger and erase the `closes` rows. The README already says the ledger doesn't guard against this.

- IMPACT: patch — the factory's CONFIRM bar and `land-check`'s `issue` signal now hold for a change whose build edits `closes:` out of its own intent. Nobody holding the previous release has to do anything differently.

**Undone items**
- UNDONE: pre-existing: none found. → dropped: it records that nothing was found, so there is nothing to carry.
