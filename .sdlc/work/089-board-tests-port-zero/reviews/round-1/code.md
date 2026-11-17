VERDICT: PASS

- PREEXISTING: plugins/factory/scripts/factory.py:2497: `_free_port()` has the same pick-then-bind window this change closed in the board tests. It serves the UI review's dev server, which is given `{port}` and can't bind 0 itself. The builder's decision D1 defaults to a seed of its own, but no such seed is in `inbox.md` yet.

## Notes

- **Port 0 on the CLI.** `cmd_board` builds its printed URL from the `--port` argument, so `board --port 0` now serves on an OS-chosen port while printing `http://127.0.0.1:0/`. Before this change that path served nothing usable, so the URL was already wrong. The spec only promises that fixed non-zero ports behave as today. The simplest fix is to print the bound port, or refuse 0, in a later change.
- **Redundant lookup in the test.** `test_the_board_answers_three_gets_and_nothing_else` recomputes `port = int(url.rsplit(":", 1)[1])`, but the fixture already yields the port as its third item. Using that would be clearer.
- **Placeholder handler in `serve()`.** `_Server((HOST, port), BaseHTTPRequestHandler)` followed by `server.RequestHandlerClass = ...` works, because `socketserver` reads the class per request. A one-line comment saying why the handler is set after binding would stop a later reader from "fixing" it.
- **The "three parallel runs" claim is not evidenced.** `build/round-1.gate.md` records one `./check.sh` pass. I ran `pytest -n auto tests/test_board.py` once (40 passed) and the single rebinding test (passed). I can't confirm the flake-freedom claim from one run, so it stays unverified.
- **Unfiled decision.** D1 says the `factory.py` seed is "haven't filed". Filing it, or deciding now that it's dropped, is for the person at ship, not something a reviewer can settle.

## What's done well

- The change is small and matches the spec. `_free_port()` and its `socket` import are gone. `served` binds port 0 and reads the real port back. `serve()` builds the host allow-list from `server.server_address[1]`, so the rebinding check keeps its meaning.
- The new assertions are the right ones. `127.0.0.1:0`, `localhost:0` and a bare `127.0.0.1` must all 404, and `localhost:<real port>` must 200. Against the old `serve()`, the 200 assertion would fail, so the test can fail.
- The check in `checks.md` passes: `_free_port` is absent and `board.serve(repo, 0)` is present.

## Tests and commands run

- `uv run --group dev pytest -q -n auto -p no:cacheprovider tests/test_board.py`: 40 passed.
- `uv run --group dev pytest -q -p no:cacheprovider tests/test_board.py::test_the_board_answers_three_gets_and_nothing_else`: passed.
- The `checks.md` command: passed.
- I did not run `./check.sh` again. The round-1 gate record shows it passing with the same build.
