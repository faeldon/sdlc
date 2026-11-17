---
id: 089
slug: board-tests-port-zero
tier: 1
impact: none
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-14
depends_on:
reworks: [075]
serves: none
---

# 089 — The board's tests bind port 0, leaving no window for another worker

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

`tests/test_board.py`'s `served` fixture picks a port with `_free_port()` (`:388-391`): it binds a
socket to port 0, reads the number the OS gave, and closes it; only then does
`board.serve(repo, port)` bind that number. Since 082 (2026-11-17) the gate runs pytest across every
core (`-n auto`), so between the close and the bind another worker can take the port, and `serve()`
raises `OSError` or binds one another test's board is on: a red gate for no fault in the change. It
hasn't failed yet (082's notes flagged the window), but a flaky gate costs every change a rerun and
every factory round a red-gate fix.

It can't simply serve on port 0, because `_handler(root, port)` (`scripts/board.py:353-354`) builds
its allowed `Host` headers from the port it's given before anything binds
(`{"127.0.0.1:<port>", "localhost:<port>"}`), so port 0 would refuse every request.

## Outcome

- `served` binds port 0 itself, through `board.serve(repo, 0)`, and reads the real port back from
  the server: no gap between choosing a port and binding it, and `_free_port()` is gone from the
  tests.
- `serve()` builds the handler's host check from the port it actually bound, so a board on port 0
  answers on its real port and still refuses another host (the rebinding check). `cmd_board`'s
  fixed `--port` path behaves exactly as today.
- Every test in `tests/test_board.py` passes, the routes, rebinding, no-write and second-board tests
  included, in three parallel runs in a row (`pytest -n auto tests/test_board.py`, three times).
- `./check.sh` passes.

## Affected

- **Area:** the board's server and its tests.
- **Files & components:** `scripts/board.py` (`serve()`, `_handler()`), `tests/test_board.py`
  (`_free_port()`, `served`).
- **Downstream:** the gate, through these tests; `sdlc.py board` and `/sdlc:dashboard` keep their
  fixed `--port`. `scripts/board.py` is a `[ui]` path, so a factory run on this change gets the ui
  and ux reviewers, though nothing on the page changes. 086, open, edits the same two files: the
  overlap is text only, and ship's `base` rebases whichever lands second.
- **Contracts:** AGENTS.md's *The board* (`127.0.0.1` only, three GETs, a request naming another
  host a 404, writes nothing): the rebinding guard keeps its meaning, keyed to the bound port.

## Constraints

- The host check never loosens: no request naming another host or port is answered.
- `cmd_board`'s behaviour on a fixed port (a board already there reported, anything else refused,
  naming the port) is unchanged.
- Tests stay `portable` where they are: binding port 0 works on Windows too.

## Open questions

- `plugins/factory/scripts/factory.py`'s own `_free_port()` (`:2427`) picks a port for the UI
  review's dev server the same way, where the server is an outside command given `{port}` and can't
  bind 0 itself: this change's window, or a seed of its own?
- Does `serve()` return the bound port, or does the caller read `server.server_address[1]`? The
  second needs no new return shape.

## Approach

In `scripts/board.py`, have `serve()` bind first and build the handler's hosts from
`server.server_address[1]` (or the handler read its port from `self.server` per request). In
`tests/test_board.py`, drop `_free_port()` and have `served` call `board.serve(repo, 0)` and use the
port it bound. Run `pytest -n auto tests/test_board.py` three times, then `./check.sh`.
