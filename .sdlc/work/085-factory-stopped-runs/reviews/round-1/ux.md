VERDICT: PASS

## Notes

**Read:** both board screenshots (1280×800 and 390×844), `intent.md`, the `stopped` handling in `scripts/board.html` and `scripts/board.py`, and the stop reading in `scripts/sdlc.py`. I did not read `decisions.md`, `spec.md`, `plugins/factory/skills/build/SKILL.md` or the status skill, so I did not check the status wording against the spec, or R10 itself. I also did not read the tests or the factory script.

**Not visible:** the screenshots show no stopped run. Card 078 is a Needs-you card for an ESCALATE, not a stop. I judged the stopped state from the code:
- A stopped run lands in the **Needs you** column (`column()` in `board.py`).
- The card flags each of the stop's problems as `stopped: <problem>`, in the same red `flag` style as the existing flags.
- Its `next:` line is the stop's own sentence, whether ship, mend or rerun. That is the person's next step, in their terms.
- A stop record that won't read becomes a problem line, so the card still shows up under Needs you rather than going blank.
- The column's subtitle now reads "a decision, a problem or a stopped run".

**Smaller findings, none blocking:**
1. At 390px the Needs-you column is last and sits below the fold, so a stopped run is easy to miss on a phone. The column order is not something this change introduced, so I'm not filing it as a change.
2. Every flag is a plain `div`, so a screen reader hears "stopped: …" only as text. It matches the existing flags, so it's consistent, not a regression.
3. A card with several stop problems stacks one `stopped:` line per problem. That is fine for the one or two problems on 078, but a long list would make the card tall.

**Done well:** the stop is worded once, by `factory.py`, and the board and status only read it. The card's flag, the column and the `next:` step all agree on why the run stopped and how to move it on. Running, deciding and ready cards still read as they did before, as the screenshot of 085 shows.
