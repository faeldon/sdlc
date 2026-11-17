VERDICT: PASS

No CHANGE or DECISION points. The 1280px and 390px screenshots show what the spec asks for, and the code covers the states the screenshots don't.

- PREEXISTING: scripts/board.py:652: the Needs you card for 006 says `needs you: stopped: mend` and `mend` is never explained to the person. The word comes from the factory's stop rules, not this change, so it belongs to a later change.

## Notes

**Read:** both screenshots (`land-1/index-1280x800.png`, `index-390x844.png`), `intent.md`, `spec.md`, `build/land-1.md`, `scripts/board.html`, `scripts/board.py`, and the `tests/test_board.py` and `docs/REFERENCE.md` lines that name the changed behaviour. `decisions.md` does not exist in the folder. I could not run `git diff main`, because the Bash tool is not available to me. I reviewed the four changed files as they now stand. `build/land-1.md` says the only conflict was in `.sdlc/work/inbox.md`, which is not one of the changed paths.

**Screenshots:**
- At 1280px, each column's subtitle ("intent", "spec", "the gate and the review", …) sits on its own row under the heading. This is the 052 fix, and the spec's first outcome holds.
- At 390px, Needs you leads the stack, as the code intends. Its cards read top to bottom with the next step last, and the card is usable.
- No column is empty in either shot, so the empty-column text is not visible. From the code, every empty column shows "nothing waiting here" at both widths, which meets the spec's words.

**States I judged from the code, not the screenshots:**
- *Stopped record that won't read:* the card gets `stopped: <problem>` and `needs you: stopped: read runs/stopped.md`, and the next step is "read runs/stopped.md". This matches `status`'s wording, as the spec asks.
- *Build with a problem and a pending decision:* the next step reads "decide D1 in the factory's supervisor, and fix what its problems name". The problems are also flagged in red on the card, so the person can see what "its problems" means.
- *Rebasing:* the next step says `--abort` keeps the work under `refs/sdlc/end/<branch>`. The ref is internal, but the spec asks for it, and the sentence attaches it to `--abort` clearly.

**Reach:** the cards are buttons, the empty and stacked states are text, and the drawer trap is unchanged by this change. I could not test keyboard focus in a browser.

**Does well:** the `.col-head` grid puts the subtitle on its own row at every width, verified by the 1280px screenshot. The next step for a card with both a problem and a decision names both, in the order the card reads.
