VERDICT: CHANGES

- CHANGE: [correctness] docs/RETRO-SCORECARD.md:465: The Hosts section still reads "The scorecard reaches hosts when S14 and S15 build it into the plugin". Both seed ids now point at nothing, and "when … build it" is stale, since the waves have landed. The intent's aim is a framework with no plan ids left in it. Reword it without ids or a future tense, for example "The scorecard reaches hosts by way of the plugin, and each part goes where a host already finds its kind:".
- CHANGE: [correctness] docs/RETRO-SCORECARD.md:154,156,481: Three more seed ids and change numbers are left in the prose: "captured (S10, 175)" twice in the Feedback-loop and Landing time bullets, and "(S1)" in the lead-time paragraph. They are not `**Status:**` lines, so the Outcome's wording technically spares them. But the Problem names ids that "point at nothing" as the defect, and the plan they refer to is deleted. Drop the parentheticals, keeping the rest of each sentence. This is a Constraints trade-off: the framework text is to stay word for word, apart from the Status lines. Removing the ids is the smaller deviation.

## Notes
- All 36 Status lines now read *captured* or *not captured: …*, with no `S`/`R` ids or change numbers. The synthesis-questions table is intact for `tests/test_retro.py:4901`.
- The opening note no longer mentions the seeds.
- The wave-based release block in `.sdlc/SDLC.md` is removed cleanly, and the `CONTRIBUTING.md` row is trimmed.
- `.sdlc/work/226-scorecard-framework-only/build/round-1.gate.md` records the gate as PASS. I ran no tests myself.
- NIT: .sdlc/DIRECTION.md:167: says "the scorecard work (waves 0–5)", which is now only history, since the waves section is gone from the scorecard. It is harmless, but "waves" no longer has a referent in the docs. {docs S low}
