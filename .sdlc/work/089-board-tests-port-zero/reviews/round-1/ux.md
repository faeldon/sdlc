VERDICT: PASS

This change alters no page a person sees. The two screenshots show the board as it stood before this change, and nothing in `scripts/board.html` changes. The edits are to how the server binds its port (`serve()` in `scripts/board.py`) and how `tests/test_board.py` starts its server, so the flows, states and labels in the screenshots are untouched.

- `serve()` now reads the bound port back from `server_address`, and `_handler()` gets that port, so the `Host` check still answers only the real port and still refuses other hosts. A person using the board on `127.0.0.1` sees no difference.
- `cmd_board`'s fixed `--port` path is unchanged, including its refusal text ("port N is in use by something other than a board: pass --port <N>") and the "already" report for a board already there. Those are the only messages a person could see from this change, and they are the same as before.

## Notes

- **Read:** `index-1280x800.png` and `index-390x844.png` (the board at desktop and phone width), `intent.md`, `decisions.md` (D1 is a default to file a seed for the factory's `_free_port()`, not a UX question), `scripts/board.py` (`_handler`, `serve`, `cmd_board`), and `tests/test_board.py` (the `served` fixture and its callers). I did not read `spec.md`: the change folder has none at Tier 1, and the intent's Outcome serves as the spec.
- **States:** no loading, empty or error state is added or changed here, so none is judged for this change. The phone layout stacks the columns and stays usable, as before.
- **Not this change's, filed for later:** `scripts/board.html:280` renders an empty column as a bare "—". The DESIGN, TEST, READY TO SHIP and READY TO CLOSE columns in the screenshots show only that dash, so nothing says the column is empty or what puts a change there. PREEXISTING: `scripts/board.html:280: an empty column shows only "—"; say nothing is in this stage yet`.
- **Done well:** the fixture now binds port 0 through the same `serve()` that production uses, so there is no gap between choosing a port and binding it, and the test exercises the real host check rather than a copy of it.
