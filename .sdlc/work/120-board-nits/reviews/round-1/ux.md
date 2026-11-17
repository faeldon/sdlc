VERDICT: CHANGES

- CHANGE: plugins/factory/scripts/factory.py:1985: `WAYS_WHY["mend"]` puts "mends it once" into the drawer text, the same jargon this change removes from the needs-you line (seed 84 says "mend" is not a word a person knows). Say it in the person's terms, for example "Rerunning /sdlc-factory:build {id} asks an agent again, once, for the reply in its shape".

- DECISION: [default] Keep the builder's D1 and D2 as they stand. Shortening `WAYS` itself is what the card and `status` need, and the imperative needs labels read well. I would not change either.

## Notes

**Read:** both screenshots (`index-1280x800.png`, `index-390x844.png`), `intent.md`, `plan.md`, `decisions.md`, `factory.py` `WAYS`/`WAYS_WHY`/`STOPPED`, `sdlc.py` `FACTORY_STOP_NEEDS`/`factory_stop()`/`needs_of()`, `board.py` `_progress()` and `next_action()`, the `.next code` and `.needs` rules in `board.html`, and the `status` skill and REFERENCE text that describe the stop lines. I could not run anything, so I judged the states from the code and the screenshots.

**States I could see:** the stopped card (006) at both widths, and the needs-you line for a stop in plain words ("needs you: stopped: rerun to ask an agent again"). The wrapping holds: the long `next:` text stays inside the card at 390px.

**States I could not see:** an empty board, loading, and a fresh stop written by the new `WAYS`. The empty and loading states are not touched by this change.

- The 006 card still shows the old long `next:` (about nine lines at 390px). Its `runs/stopped.md` was written before the change, and the board reads the record's `NEXT:` line. The short text appears only on the next stop, so the "line or two" outcome is not visible in these shots. Worth knowing when the shots are read at ship.
- The fresh `mend` next line, "rerun /sdlc-factory:build 006, or /sdlc:ship 006", is about 49 characters, which is two lines of monospace at 390px. That meets the outcome.

**Smaller findings:**
- Same step, two verbs in one card: the needs line says "review an agent's commit" and the `next:` line says "read the commit, then /sdlc:ship". Pick one word for both.
- A stop card names "stopped:" twice, once on the red flag line (`board.html` line 266, from 110) and once on the needs line. Not this change's, so filed for later: PREEXISTING: scripts/board.html:266: a stop card reads "stopped:" on its flag line and again on "needs you: stopped:".
- The `rerun` needs label, "fix its cause and rerun", reads fine beside "its" meaning the change. No change needed.

**Done well:** the needs labels are short imperatives with no comma, so `status` joins them safely, and the stop record keeps its shape so the drawer and `status` read it as before. The longer explanation goes to the record body, where it is a click away instead of crowding the card.
