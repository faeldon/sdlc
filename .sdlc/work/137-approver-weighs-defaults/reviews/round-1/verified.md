- KEPT: ux: C1: scripts/board.py:636: at `test` with open items the next step never names `/sdlc-factory:decide NNN`. A change with only defaults to confirm falls through to the "/sdlc:ship, or land" line at 640 and skips the confirmation.
- KEPT: ux: C2: scripts/sdlc.py:4383: status's "confirm N default(s)" need doesn't say where to do it, and `/sdlc-factory:decide` appears nowhere in its hint.
- KEPT: ux: C3: plugins/factory/skills/decide/SKILL.md:35: the refusals only say "say so and stop". The not-at-`test` case does give the reason (the supervisor asks its own blocking decisions), but it gives no next step. A bad or unknown NNN has neither.

## Notes
I ran nothing. I read `board.py` lines 615–660, `needs_of()` in `sdlc.py`, and the decide `SKILL.md`. C3 is the weakest of the three: the not-at-`test` refusal already explains itself, so only the missing "what to do instead" and the bad or unknown NNN case are open.
