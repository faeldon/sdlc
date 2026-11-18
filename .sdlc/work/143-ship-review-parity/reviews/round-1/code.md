VERDICT: PASS

I read the diff against spec R1–R24. `./check.sh` passes: ruff is clean, 2601 tests pass with 18 skipped, and both `claude plugin validate --strict` runs pass. The factory plugin gets one warning about a missing icon, and the check does not fail on it. I found nothing at Critical or Required level.

## Notes
- NIT: skills/ship/behaviour.md:3: the line says "whose own behaviour reviewer ran" and security.md and ui.md say the same of their factory reviewers. Only the factory case is meant, so "a factory run, whose own reviewers ran" would match `_passes_report()`'s wording. {docs S low}
- NIT: skills/ship/security.md:3: it says the pass applies when the diff touches a `review.sensitive` path. The script keys on `risk.deep`, so the sentence is only as exact as `deep` is. Say "a deep diff" to follow R2. {docs S low}
- NIT: scripts/sdlc.py (`_passes_report`): `cmd_preflight`, `cmd_ship` and `cmd_ship_question` each call it, so `git show` and `changed_paths` run three times per ship. That is harmless at this size, but it could be cached per run if ship slows down. {robustness M low}
- Done well:
  - Every condition is in `_passes_report()`, and the side files only say how to run a pass.
  - `[ui]` is read from the base branch.
  - A screenshot set is rejected when it is stale, missing a PNG or has a `problem`, and the reason is reported.
  - The `passes=` trailer keys come after `agents=`, so older trailers keep their shape.
  - `## Evidence` is parsed apart from findings.
  - The three new agents have exactly `Read, Grep, Glob`.
  - The AGENTS.md policy edit (R24) is made and matches the code.
  - The "one agent" wording appears nowhere else in the docs I searched.
  - `SKILL.md` stays at the 475-line budget.
- Ran: `./check.sh` (all of the above).
