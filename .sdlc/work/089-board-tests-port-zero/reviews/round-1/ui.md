VERDICT: PASS

No screenshot shows this change, and the change doesn't touch anything the board draws. `scripts/board.py` moves the rebinding host check in `serve()` and `_handler()` to the port the server actually binds, and `tests/test_board.py` stops picking a port in advance. `scripts/board.html` and every stylesheet are untouched, so the page renders as it did before the change. Both screenshots show the board as it stands, and I judged only what they show.

## Notes

Screenshots read:
- `index-1280x800.png`: the desktop board, with the columns Plan, Design, Build, Test, Ready to ship, Ready to close and Needs you, and the Build column's factory card.
- `index-390x844.png`: the phone width, with the columns stacked vertically and the cards reading in one column.

Read with them: `intent.md`. There is no `spec.md`, since this is a Tier 1 change and its Approach is in the intent.

Smaller points, none a CHANGE:
- The intent's Open questions ask whether `serve()` should return the bound port or whether the caller should read `server.server_address[1]`. The Approach leaves that to the builder, and it is an interface choice, not a look, so it isn't mine to raise here.
- The `_handler()` change should keep the host check's refusal of a request naming another host or port. The intent's Constraints already say so, and the tests the intent names (rebinding, no-write, second board) are the check for it. I can't confirm from screenshots that they still pass.

What the change does well: it removes the gap between choosing a port and binding it, rather than widening the allowed hosts to get around the port-0 problem, so the rebinding guard keeps its meaning.
