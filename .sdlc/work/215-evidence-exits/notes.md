# Notes

> 215's builder notes: what was found on the way and left out of the change.

## Open questions, as built

- AGENTS.md's wording stays: it states the script's rule, which this change keeps as it is. The
  prompts ask for more than the script needs; the factory README now says both.
- Only `builder.md`, `resolver.md` and `reviewer-behaviour.md` end with an `## Evidence` section.
  The other reviewers' `Evidence:` is a field of each finding, never read by `read_evidence()`, so
  they need no line (`test_no_agent_prompt_lets_a_read_leave_its_exit_off` pins the three).

## Nits

- 2026-11-20-61: taken, in `cmd_accept()`. `cmd_gate()` already checks its record again after the
  slot wait and the run (199's round 2); accept had the same gap after `sdlc.py accept` ran.
- 2026-11-20-47: not taken (raised as a decision). The fork point holds no `intent.md` for a
  factory run: the change's folder is untracked until ship commits it, so a read there gives no
  `closes:`, which would let every change carry a `- CONFIRM:` the intent bars. Closing it needs
  the approved `closes:` recorded somewhere the build can't write, such as the records ledger at
  `start`.
- [x] Record the intent's `closes:` at `start` in the records ledger, and have `intent_closes()` → seed: 2026-11-21-42
  read the union of it and the working copy (nit 2026-11-20-47, done right).
