# Decisions

- [x] D1 (builder round 1, default): Serve the fixture in-process (`build.sh` plus `board.serve(root, 0)`) rather than through `serve.sh` as the Approach says. Going ahead unless told otherwise. → settled by the approver: `plan.md` says why the test serves the board in-process instead of through `serve.sh`: the OS picks the port, so parallel test workers don't race for it, and the server is shut down in a `finally`. That is what the intent's constraint requires ("stops the server however the test ends"). The code, security and test reviews of round 1 each confirm the server binds `127.0.0.1` on a port the OS picks and always shuts down.
  - OPTION: in-process — the OS picks the port, so no race between parallel test workers, and the server stops in a `finally`; it doesn't exercise `serve.sh`'s own lines
  - OPTION: `serve.sh` subprocess — the exact command the UI review runs; the port has to be chosen before it's bound, which can race, and a child process has to be killed
  - WHY: the intent's constraint that the server stops however the test ends, and `tests/test_board.py`'s `served` fixture already serves this way
- [x] D2 (builder round 1, default): Chromium alone, not WebKit too (the intent's open question). Going ahead with Chromium only. → decided: the assumed default, confirmed
  - OPTION: Chromium alone — one download in CI and locally; Safari's focus handling isn't covered
  - OPTION: Chromium and WebKit — covers Safari too; a second, bigger download and a slower CI job
  - WHY: the intent's Approach names Chromium, and the trap is plain DOM focus code
- [x] D3 (builder round 1, default): No extra note in `./check.sh`'s summary when the browser test skips (the intent's other open question): pytest's "N skipped" count and `-rs` give the reason. Going ahead unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: no extra note — `check.sh` stays as it is; a contributor has to know about `-rs` to see why
  - OPTION: add `-rs` to `check.sh`'s pytest call — every skip's reason is printed; noisier output on every run
  - WHY: CONTRIBUTING's new paragraph says the test skips and how to install the browser
