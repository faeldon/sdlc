# Decisions

- [x] D1 (builder round 1, default): Move `decision_preamble` into `run_state.py` too, beyond R1's list of eight? Going ahead with moving it unless told otherwise. → settled by the approver: R1 says its list is "the named entry plus every function that only it calls today, by the rule in R3", and only `loop_state` calls `decision_preamble`. The R3 test asked for the move, and round 1's AST comparison (security) shows `decision_preamble` moved unchanged. The code, test, security and behaviour reviewers all raised nothing on it.
  - OPTION: move it — R3's rule holds both ways and R1 says that rule decides the list; the module has nine functions, not eight
  - OPTION: keep it in `factory.py` — matches R1's list word for word; needs an exception in R3's test, which then no longer holds both ways
  - WHY: R1 says its list is "the named entry plus every function that only it calls today, by the rule in R3", and only `loop_state` calls `decision_preamble`.
- [x] D2 (builder round 2, default): R14's deadline is 120 s, not the spec's 60 s. Going ahead with 120 s unless told otherwise. → settled by the approver: Round 1's behaviour review showed the 60 s deadline fails falsely: 71 s alone on this build, against 79 s at the merge base under the old 120 s wait. Round 2's code, test and behaviour reviewers each passed it at 62–65 s under 120 s. The test still exits as soon as `.started` appears, so a fast machine waits no longer. `plan.md` (R14 line) records why it departs from the spec.
  - OPTION: 120 s — fits a loop's startup under load, as a gate shared with other builds has; a real hang takes a minute longer to fail
  - OPTION: 60 s, as the spec says — fails faster on a real hang; failed falsely in round 1 when the loop started slowly under load
  - WHY: the behaviour review's failed run used up the 60 s deadline before the reviewer started, while the same test passes at the merge base with its old 120 s wait.
