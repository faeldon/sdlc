# Decisions

- [x] D1 (builder round 1, default): Record `closes:` in `factory.py agent` as well as `start`? Going ahead with both unless told otherwise. → settled by the approver: The Outcome says what a change closes is fixed "before any agent runs", and plan.md and the builder's report show autopilot never runs `start`. Recording in `agent` as well is therefore the Approach's own intent, which the code and security rounds endorsed, and it adds no scope, policy, cost or interface.
  - OPTION: start and agent — covers autopilot, which never runs `start`; it re-reads the ledger on every agent call, but only appends once per value
  - OPTION: start only — exactly what the Approach says; autopilot runs, the ones D9 relies on, record nothing and a build could still remove `closes:` there
  - WHY: the intent's goal is that what a change closes is fixed before any agent runs, and autopilot reaches its agents without `start`
