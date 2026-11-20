# Decisions

- [x] D1 (builder round 1, default): Make the guard the unused-fixture check? Going ahead with it. → settled by the approver: The intent's Outcome asks for "one helper or fixture" against the commonest kind of `tests` nit. The unused-built-in-fixture check is the commonest kind the gate can judge, and `notes.md` (*The guard against the commonest kind*) says why the alternatives fall short. The round-1 code review confirms the guard tests its own detector both ways. It is test-only and touches no scope, policy or published interface.
  - OPTION: unused built-in fixture — catches the commonest kind of tests nit a script can judge; it doesn't catch weak assertions
  - OPTION: a docstring on every test helper — the kind -7 is; 431 helpers lack one today, so it would mean a huge change
  - OPTION: none, weak assertions only — those are the commonest tests nit overall, but only a reviewer can judge them
  - WHY: the intent asks for one helper or fixture against the commonest kind, and this is the commonest kind the gate can hold
