VERDICT: PASS

## Notes
- Tier 1 with no `spec.md`. Reviewed against the intent's Outcome: `.sdlc/SDLC.md` says when this repo releases, and the guide's rule isn't restated.
- NIT: .sdlc/SDLC.md:83: the new block names no number of changes or days. The "once each wave has landed" rule is fine, but a person may wonder what to do if a wave stalls past the 14-day mark. One clause would settle it. {docs S low}
- Done well: the block sits under `### The release loop → /sdlc:release, then /sdlc:publish`, a heading `guide/process.md:408` has, as the "holds only its answers" invariant requires. It answers that slot and leaves out the guide's Release due rule.
- The pointer to `docs/RETRO-SCORECARD.md`, *Waves* resolves: the heading is at line 538.
- Context pass: no other context doc says anything about release timing that this diff makes false.
- Ran nothing. `build/round-1.gate.md` is `GATE: PASS` for `./check.sh`, so the `tests/test_defaults.py` checks on the process doc passed.
