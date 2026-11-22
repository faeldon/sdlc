# Decisions

- [x] D1 (builder round 1, default): Pin R7 at two `recorded_closes()` reads per agent run, not the spec's one, and leave the code as it is. Going ahead with two unless told otherwise. → settled by the approver: The code reads `recorded_closes()` twice per agent run, once from `loop_state()` via `intent_closes()` and once from `record_closes()`. The spec's count of one was wrong. `plan.md` explains the departure, `build/round-1.md` and its docstring state it, and the test reviewer accepted it. The test would still catch a third read, and the cost is a small file per agent session.
  - OPTION: pin two, no code change — matches what runs today and still catches a call added in a loop; the spec's count was wrong
  - OPTION: pass the reading's closes into `record_closes()` so there is one read — matches the spec; changes how `loop_state()` and `cmd_agent` share data for no real saving
  - WHY: R7 is about cost, and a second read of a small file per agent session costs nothing worth new code paths
