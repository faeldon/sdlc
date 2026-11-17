---
id: 089
slug: board-tests-port-zero
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 089 — The board's tests bind port 0, leaving no window for another worker · plan

> Written after reading `scripts/board.py`'s server and `tests/test_board.py`'s `served` fixture.
> Tier 1: the intent's Approach is the spec; this records how it was built.

## Files to change

- `scripts/board.py`: `serve()` binds first, then sets the server's handler from
  `_handler(root, server.server_address[1])`, the port it actually bound. `_handler()` is reused
  unchanged; `cmd_board()` is untouched, so a fixed `--port` binds and checks exactly as before.
- `tests/test_board.py`: `_free_port()` and the `socket` import go; `served` calls
  `board.serve(repo, 0)` and reads the port from `server.server_address[1]`. The routes test also
  asserts a `Host` naming port 0 (or no port) is refused and `localhost:<bound>` answered.
- `.sdlc/work/089-board-tests-port-zero/checks.md` (new): `_free_port` stays out of the board's tests.

## Work order

1. One slice: the fixture on port 0 (red: every served test 404s, the hosts keyed to port 0), then
   `serve()` keyed to the bound port (green), then the board's tests three times under `-n auto`,
   then `./check.sh`.

## Tests

- Outcome 1 (no gap, `_free_port()` gone): the `served` fixture itself, and `checks.md`.
- Outcome 2 (answers on its real port, still refuses another host):
  `test_the_board_answers_three_gets_and_nothing_else`, with the added `127.0.0.1:0`,
  `localhost:0`, bare-host and `localhost:<port>` cases.
- `cmd_board`'s fixed port unchanged: `test_a_second_board_reports_the_first_and_anything_else_is_refused`.
- Outcome 3: `pytest -n auto tests/test_board.py` three times; outcome 4: `./check.sh`.

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, and no data or published
interface changes (`serve()` keeps its signature and return type).
