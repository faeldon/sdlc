VERDICT: PASS

This change has no page of its own. The only screenshots are the board at 1280 and 390 wide, and the board code changed only so that `upgrade` and `spec` count as pauses on a card's step track. I read the 1280 screenshot, `intent.md` and the `PAUSES` change in `scripts/board.py`.

## Notes
- **Not read:** I did not read the 390 screenshot, `spec.md`, `decisions.md`, or `factory.py`, `build/SKILL.md`, `README.md` and the builder prompt. So I did not check the supervisor's path through an upgrade, the wording of the spec question, or whether the records name the round and the reason.
- **Board:** the 1280 screenshot shows no card in an upgrade or spec pause, so I judged that case from the code only. A paused card keeps the track position it paused at, as a `decide` pause already does, so the person still sees where the run stopped.
- **Reach:** nothing in the board changes how a control is reached or named, and I saw no new control. The 390 layout is unviewed.
- **Strength:** the intent states the outcome as one stop for the person, at the spec, instead of the supervisor moving the stage by hand. Reusing the `decide` pause behaviour on the board keeps the cards consistent.
