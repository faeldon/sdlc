VERDICT: PASS

- DECISION: [default] (build-stage) Should a blocking decision on a card at `build` name `/sdlc-factory:decide NNN for D1`, as the intent's outcome says? Assuming no, because that command refuses a run that is still building.
  - OPTION: keep "decide D1 in the session running /sdlc-factory:build NNN (rerun it if that session ended)" — it is accurate while the run is building, and the person is sent to where the question is actually asked. It is long, and the card never says `/sdlc-factory:decide` at that stage.
  - OPTION: show `/sdlc-factory:decide NNN for D1` at every stage — it matches the intent word for word and is shorter. It sends the person to a command that refuses them while the run is still building.
  - OPTION: show both, with the session wording first and `/sdlc-factory:decide NNN for D1` once the run has stopped — each stage gets the right command. It adds a branch to `next_step()`.
  - WHY: a next step that the command refuses is worse than a longer line. `board.py:755` records that `decide` refuses a build in progress, so the card follows the code.

## Notes

I read:
- both screenshots (1280 and 390 wide);
- `intent.md`;
- the changed parts of `board.py` (`next_step()`, lines 745–811) and `board.html` (round labels and flags, lines 410–458).

I did not read the other changed paths: `sdlc.py`, `factory.py`, the tests and the docs.

I judged these from the code, because the screenshots don't show them:
- **Stopped landing:** it sits in Needs you with the way on. `/sdlc:close NNN` shows on a shipped card, `/sdlc:ship NNN` otherwise. Each stop reason is a plain `landing stopped: …` flag.
- **Early stops:** `stuck` and `untestable` have their own plain "stopped early: …" flags.
- **Round labels:** build rounds read `B1`, `B2` and landing rounds `L1`. The labels are consistent across the chips and the track heading, and `R` no longer clashes with requirements.
- **Phone width:** at 390px the board becomes one stacked column, with Needs you first, and the person can still read each card's way on.
- **Not reviewed:** I did not check whether the "stopped" and rebase-in-progress states show properly on a card at phone width. The fixture has no such card in view.

Smaller findings:
- The rebase-stopped `next` line (`board.py:748`) is raw jargon: "sdlc.py resolve NNN --continue … refs/sdlc/end/…". The intent asks for plain stop lines, and this line carries the ref path in the instruction.
- Flag text such as "kept two rounds running" is understandable. In the stuck case it still doesn't say what to do next.

What the change does well: the Needs you column is now where a stopped landing sits, and every card ends with a concrete next command. The same label vocabulary (`B`, `L`) appears in the chips, the track heading and the "of N" count.
