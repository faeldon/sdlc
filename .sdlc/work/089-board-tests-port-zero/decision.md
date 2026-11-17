DECISION: ESCALATE

**Why.** The build is done and every reviewer passed it in its one round: code, ui and ux all returned `VERDICT: PASS`, the gate passed, and the builder's evidence shows the board's tests passing 40/40 in three parallel runs in a row, plus a full `./check.sh`. I'm escalating anyway, because decision D1 is still unticked: the build rests on an assumption you haven't confirmed. That assumption also left a pre-existing problem unfiled, so it is only in `notes.md`. There is a second reason to look: the rebase onto `main` ran into a conflict and it was resolved (`conflicts.md`: `.sdlc/work/inbox.md` onto 95a03ee), and a resolved conflict is yours to check.

**Open items**
- [ ] `notes.md` / code reviewer (PREEXISTING): `plugins/factory/scripts/factory.py:2497`'s `_free_port()` has the same gap between picking a port and binding it. No seed for it exists in `inbox.md` yet.
- ux reviewer (PREEXISTING, not in `notes.md`): `scripts/board.html:280` shows an empty column as a bare "—". It needs a disposition at ship, or a `/sdlc:bug` / `/sdlc:idea` entry.
- code reviewer (a note, not a CHANGE): `board --port 0` now serves on a port the OS picks, but `cmd_board` still prints `http://127.0.0.1:0/`. Before this change that path didn't work at all, so this is a candidate for a later seed (print the bound port, or refuse 0).

**Decisions to confirm**
- D1: should `factory.py`'s `_free_port()` (which picks the port for the UI review's dev server) be fixed here or get its own seed? The build assumed its own seed, which hasn't been filed. The reason given is that the dev server is an outside command handed `{port}`, so it can't bind port 0 itself. Confirming D1 means filing that seed (or dropping it with a reason) and ticking the `notes.md` line.

**For the person at ship**
- Look at the `.sdlc/work/inbox.md` hunk in the diff first. That is the conflict that was resolved, and the builder says the worktree had already modified it before the build began. Make sure no register entry was lost or changed, and that nothing from the inbox rides on this branch when it shouldn't.
- Then `scripts/board.py`'s `serve()`, lines 686–692. It binds using the plain `BaseHTTPRequestHandler`, then swaps in `_handler(root, server.server_address[1])`. This works because `socketserver` reads the handler class on each request, and no request is served before `serve_forever()` runs. The reviewer suggested a one-line comment explaining why the order matters.
- Then the new host cases in `test_the_board_answers_three_gets_and_nothing_else`: `127.0.0.1:0`, `localhost:0` and a bare host get a 404; `localhost:<bound>` gets a 200. These keep the check against DNS-rebinding requests tied to the port the server actually bound.

- IMPACT: none — the change is to test plumbing and the port the board's own server checks against. A fixed `--port` on `sdlc.py board` and `/sdlc:dashboard` behaves exactly as before, so nothing anyone receives changes.
