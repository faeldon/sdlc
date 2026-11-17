VERDICT: PASS

- DECISION: [default] The intent's outcome says a stopped run's next step "reads in a line or two at phone width", but the round-3 390px shot of card 006 breaks `rerun /sdlc-factory:build 006, or /sdlc:ship 006` over three lines (`rerun /sdlc–` / `factory:build 006, or` / `/sdlc:ship 006`). It is readable and stays inside the card. Recommendation: accept three short lines, since the command names can't be shortened without dropping the `or /sdlc:ship {id}` way on, and change the outcome to "in a few short lines, not one run-on sentence". The alternative is to drop `or /sdlc:ship {id}` from the card's `next:` line, which also changes `status`'s `→` line and the stop record. The person decides which outcome the intent should keep.

## Notes

**What I read.** Both round-3 shots (`round-3/ux/index-1280x800.png`, `index-390x844.png`), `intent.md` (Tier 1, so its Approach stands for the spec; there is no `spec.md`), and `decisions.md`. In code: `factory.py`'s `WAYS`, `WAYS_WHY` and `stop_text()`; `sdlc.py`'s `FACTORY_STOP_NEEDS`, `factory_stop()` and `needs_of()`; `board.py`'s `_stopped()` and `_progress()`; `board.html`'s card render and `.next code` CSS; and the fixture `runs/stopped.md`.

**Last round's kept point is closed.** The round-3 shots show card 006's `next:` as the current `WAYS["mend"]` sentence, not the old run-on. The fixture's `NEXT:` line and body match `stop_text()` output for `mend`. I can't run the factory, so I'm judging from the shot and the fixture, not from a fresh record.

**Settled point.** `WAYS_WHY["mend"]` now reads "asks an agent again, once, for the reply in its shape". Not raised again.

**Needs-you wording.** "needs you: stopped: rerun to ask an agent again" (the 1280 shot) uses plain words. No person-facing text in `board.html` or `board.py` says "mend". `status`'s `→` line and the card's `next:` line share the same `WAYS` text.

**Reach.** Each card is a real `<button>` with its change in the text. `overflow-wrap: anywhere` is on `.next code`, and no card in either shot overflows at 390px.

**States I couldn't see.** Loading and the empty board aren't in the shots, and this change doesn't alter them. A stop whose record won't read shows `needs you: stopped: read runs/stopped.md`, a file path a person may not know. I judge it acceptable as a fallback for a broken record, not a CHANGE.

**Smaller findings:**
- The `/sdlc-factory:build` command splits at its hyphen across lines in both shots (`/sdlc–` / `factory:build`). It's still legible, and a non-breaking hyphen would paste wrongly, so I'd leave it.
- The card flag `stopped: build/round-1.md has no ## Evidence section` shows a markdown heading marker and a file path. The text comes from the factory's problem line, which this change doesn't alter. PREEXISTING: `plugins/factory/scripts/factory.py`, the problem line that names `## Evidence`, for a later change.
- Card 007's `next: decide D1 in the factory's supervisor` uses "supervisor", a factory word a person may not know. PREEXISTING unless this change altered that line; I did not see it altered in the diff I was given.
- The `rerun` way's needs label, `stopped: fix its cause and rerun`, leaves "its" without a clear antecedent on the card. Consider "fix the cause, then rerun".
- `WAYS["rerun"]`'s `next:` line leads with "fix its cause" too, so the same vague "its" recurs. Fix both together if the builder takes the last point.

**What the change does well.** The stop's way is now one short line in the shared `WAYS` text, read the same by the card, the drawer and `status`. The needs line is an instruction in plain words, and the old jargon is gone from the person's view.
