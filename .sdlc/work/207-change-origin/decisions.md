# Decisions

- [x] D1 (builder round 1, default): Fix the stale `tests/fixtures/close-output.json` in this change? It pins `plugin=1.10.0`, which Release 1.11.0 made stale, so four `test_close_output_is_unchanged` cases fail on the base branch itself (confirmed on a `git archive HEAD` copy). The gate would be red for any build. Going ahead with `_normal()` masking `plugin=<version>`, as it masks shas, unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: mask the version in this change — the gate goes green, and later releases won't break the fixture again; an unrelated test edit rides on this change
  - OPTION: revert it and fix it in its own Tier 0 change on the base branch — keeps this change narrow; this build's gate is red until that lands
  - WHY: the gate runs the whole suite on this build, and the fault isn't in this change's code.
- [x] D2 (builder round 1, default): Write `origin:` on 207's own intent? Leaving it unset, the same as 206 (the intent's open question): the line is the person's to approve through `/sdlc:intent`, not the builder's. → settled by the approver: `spec.md` says origins are never guessed or backfilled, and a missing `origin:` line reads as unknown (R2, R3). The reviewers confirmed that leaving 207's own intent unset is what the spec intends.
  - OPTION: leave it unset — reads as unknown, which is what the spec says a missing line means; 207 isn't counted
  - OPTION: `origin: self` — 207 is counted; the builder would be writing a line the person never approved
  - WHY: the spec's constraint that origins are never guessed or backfilled.
- [x] D3 (approver round 1, look): `scripts/closing.py: origin_trailer()` — this is a sensitive path, so the person should look at it before it lands. It is the only new code in close. It writes a trailer only from the two fixed words, never raises, and is called only from `_step_remove_folder()`. → decided: seen
