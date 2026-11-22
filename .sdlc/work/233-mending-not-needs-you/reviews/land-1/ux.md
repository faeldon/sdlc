VERDICT: PASS

## Notes

- **Read:** both screenshots (1280×800 and 390×844), `intent.md`, and the changed parts of `scripts/board.html` and `scripts/board.py`: the card flags, `_mend_progress()`, and the card's `next:` line for a mend.
- **Not shown in the screenshots:** the fixture has no card being mended. I judged that state from the code instead.
  - **Column and step:** a card being mended stays in Building. Its track shows `mending <role>` at the step of the role being mended.
  - **Timing:** it shows time elapsed with no typical-time bar. A mend is open-ended, so the page doesn't invent a figure.
  - **Next line:** it reads "the factory is mending the <role>: wait for it, or …". The "or …" covers the person whose session has ended.
  - **Flag wording:** the flag reads `mending: <problem>` instead of `stopped: <problem>`. The Needs-you line and the red "stopped" wording are gone for that card. That answers the problem the intent describes.
- **The stops that really are the person's:** the 006 card still shows a red `stopped:` flag, `needs you: stopped: rerun to ask an agent again`, and a `next:` line saying what to rerun. Nothing about those cards got quieter.
- **Phone width:** the 390px layout stacks the cards in one column. The flags, `needs you:` line and `next:` command wrap and stay readable. The mending state uses the same card parts, so the task still works on a phone.
- **Smaller points:**
  - A mending flag reads `mending: build/round-1.md has no ## Evidence section`. That is understandable, but "mending: " followed by the stop's reason is terse. A small `fixing:` or `mending —` phrasing would read slightly better. Not worth a round.
  - The "mending" state is shown only through the step label and the flag text, with no colour distinct from the amber or red flag styling. That's acceptable, because the words carry it.
- **Done well:** a mend that has timed out or used up its one go falls back to Needs you, so a person is never left waiting on an agent that isn't running. The card's `next:` line also still tells them what to do if the session has ended.
