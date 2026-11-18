VERDICT: PASS

## Notes

- NIT: plugins/factory/skills/build/SKILL.md:416: this line still describes `exhausted` only as "rounds ran out". It is now also true for a `stuck` or `untestable` stop. Add a clause saying the approver is told which. {docs S med}
- NIT: plugins/factory/agents/reviewer-ux.md: its diff is 5 lines, against 8 for the other reviewers. Check that the word-for-word re-raise sentence reads the same there. {docs S low}

**Requirements (R1–R10).** I found code and a test for each one.
- R1/R2: `light_reviewers()` adds `behaviour` behind the `chosen` check, and `model_for()` no longer has a haiku branch.
- R3/R5: `early_stop()` reads round files alone and only fires once the last round is complete and verified. `exhausted` then forces an `ESCALATE` with `## Reconsider the approach` in `read_decision()`.
- R4/R7: the review and approve prompts have the new sentences.
- R6: the README table covers 124, 125, 129 and 131.
- R8: `_landing_catches()` counts each change once, using the `by` and `class` fields from `findings.md`.

**Done well:**
- A reworded repeat only falls back to the round cap and never produces a wrong escalation.
- A restart or an upgrade resets the `stuck` count, because `first` moves.
- A host's own `[light]` and `[models]` settings are untouched.
- `land_verdict()` and `max_runs()` are not touched.
- The README gives the evidence for each default change.

**Not checked:** I did not read the new test bodies in full, and I did not run `./check.sh`.

**Ran:** `pytest tests/test_factory.py tests/test_retro.py tests/test_bugs.py -n auto`, 482 passed.
