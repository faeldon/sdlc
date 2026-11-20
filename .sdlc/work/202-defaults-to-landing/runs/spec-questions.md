
**Open questions resolved**

- **ESCALATE with a "defaults only" reason, or READY with the defaults carried to the landing?** READY, with a `- CONFIRM: D<n>:` line per default. The code already reads "READY with an open default" as "confirm at the landing" everywhere:
  - `ready()`, `land_signals()`, `land_question()` and `_dispose()` in `landing.py`;
  - `needs_of()` and `column()` in `sdlc.py`.

  ESCALATE would need an exception in each reader of the decision word, copied into `factory_records.py`.
- **Does `/sdlc-factory:decide` keep a path for answering defaults before the landing?** Yes, with no new path. `cmd_ask()` (`factory.py`) refuses only by stage and lists every open ledger line at `stage: test`, whatever the decision. Its `next` already gives `ship` or `rebuild` with `/sdlc:ship NNN` for a READY change. R10 pins this and adds the approver's CONFIRM reason to each item.

**Left for you**

- **Should touching a `[review] irreversible` path also block CONFIRM?** The intent names sensitive paths, policy and `closes:` only, and this spec follows it.
  - **Adding it:** every change under `defaults/` or `templates/` in this repo would stop at `/sdlc-factory:decide` again.
  - **Leaving it out (as drafted):** those defaults are confirmed at the landing, where the irreversible path is already a signal of its own.
- **AGENTS.md wording.** The design adds one cause to the list of stops a run mends (*Contracts touched*). Approving the spec approves that edit to the policy doc.
