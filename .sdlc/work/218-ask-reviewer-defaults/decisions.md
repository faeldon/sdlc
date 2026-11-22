# Decisions

- [x] D1 (builder round 1, default): A reviewer's default counts as built only when a builder report from a later round has a `- BUILT: D<n>` line for it. Going ahead with that unless told otherwise. → settled by the approver: the intent's Approach and open question call for the script to decide from the files alone. `unbuilt_defaults()` and `BUILT_RE` do that with a `- BUILT: D<n>` line from a later round. The code and behaviour reviews of round 1 checked the same-round and wrong-id cases and raised nothing against it.
  - OPTION: an explicit `- BUILT: D<n>` line — the script can check it and the builder only writes it for what it built; a builder that forgets it causes a needless rebuild
  - OPTION: any builder report after the raising round — needs no new line; it can't tell a build that made the call from one that ignored it, which is how 216 shipped
  - OPTION: the builder's own `- DECISION:` line naming the id — reuses an existing line; a decision line is a question, not a record of work done
  - WHY: the intent's open question; only a line about the work itself keeps `ask` deciding from the files alone
- [x] D2 (builder round 1, default): Leave autopilot's handling of reviewer defaults it answers for a later change. Going ahead unless told otherwise. → decided: autopilot holds such a change
  - OPTION: out of scope here — this change stays the size its Approach sets; autopilot can still land a reviewer's default nobody built
  - OPTION: autopilot holds such a change — closes the same gap; it widens 218 into autopilot's hold rules, which the Approach doesn't cover
  - WHY: `autopilot.py` never calls `cmd_ask`, so this fix doesn't reach it, and the intent leaves it as an open question
