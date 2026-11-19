# Decisions

- [x] D1 (builder round 1, default): Should the drawer test wait up to 120s for the page instead of 10s for a poll and 30s for everything else? Going ahead with 120s unless told otherwise. → settled by the approver: The intent's Approach says to "wait on the focus state, not a delay" and its Outcome says the test "waits on the state it asserts instead of on time". So the bound only has to stop a real hang. The builder showed that the 10s wait was the failure (polls held 11s fail with `Timeout 10000ms exceeded`) and that the 120s `PATIENT` bound passes. Round 1's behaviour review checked that `set_default_timeout(PATIENT)` is the file's only time limit, and both reviewers agreed with this default. It changes only how long this repo's own test waits: nothing a host receives, and no scope, policy, cost or interface question.
  - OPTION: 120s on every page step — no load or stall a gate meets should hit it; a truly broken board costs two minutes before it fails
  - OPTION: no limit at all — never fails on time; a broken board hangs the gate with no output
  - OPTION: keep 10s and make the test trigger the poll itself — shorter; still fails when a poll is slow, which is the failure we saw
  - WHY: the intent asks the test to wait on the state, not on time; a long bound only stops a hang
