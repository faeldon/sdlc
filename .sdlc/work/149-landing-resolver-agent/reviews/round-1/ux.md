VERDICT: CHANGES

- CHANGE: scripts/board.py:843: the card's `next:` line still says "its builder is resolving a conflict". After this change the resolver does that work, so the card names an agent that isn't running. Change it to "its resolver", or to a neutral "its agent". Update the same wording in `tests/test_board.py:1216` and `:1424`, and in the board paragraph at `docs/REFERENCE.md:579`. The comment at `board.py:836` already says "agent", so only the user-facing string is stale.

## Notes

- I read both screenshots (1280 and 390 wide), `intent.md` and `board.py` `next_action`. I did not read `spec.md`, `decisions.md`, the gate record or the other changed paths. The agent prompts, skills and tests are not a person-facing UI, so I did not judge them.
- The fixture board has no card in the landing-resolve state, so the screenshots can't show the wording above. I judged it from the code. The screenshots show no layout regression. The 390px layout stacks the columns, and the cards stay readable.
- The new string was also not a point I could check against the spec.
- Done well: `next_action` handles the "agent is resolving" case separately from the "rebase stopped, resolve by hand" case. Each says what to do next: wait, or rerun `/sdlc-factory:land <id>` if the session ended.
