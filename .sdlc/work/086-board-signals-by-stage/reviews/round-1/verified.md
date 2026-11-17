Verification of round 1 is finished. I read the code and probed `column()` and `next_action()` directly, and I ran no tests or checks.

- KEPT: ux: C3: scripts/board.html:256: the `ESCALATE` chip is drawn from `c.decision` whatever the stage, so an escalated change that was shipped or dropped still wears it under Ready to close.
- DROPPED: code: C1: scripts/board.py:580: `next_action()` shows a stop at the wrong stage — `entry["stopped"]` is set to None at line 168 unless the raw frontmatter stage is `build`, so a change at `test` has no stop for either function to read. Probing gave `column()` = `test` and `next_action()` = `/sdlc:ship` for that case. For raw `build` with `seen` = `test`, both say Needs you with the stop's `next`, so they agree.
- DROPPED: code: C2: scripts/board.html:247: the stopped flag is ungated — `c.stopped` is already null past `build` (board.py:168), so a shipped card never gets "stopped: …". Only a comment-wording mismatch remains, which is style.

## Notes
- **C3:** this is the only live defect. `decision` is set whatever the stage (board.py:312), and `column()` and the flags gate it to `test` but the chip does not. A Ready to close card would still show `ESCALATE` beside its `/sdlc:close` line.
- **Unread files:** `spec.md` doesn't exist because the change is Tier 1, so I judged against `intent.md`. I didn't read the new tests in `tests/test_board.py`.
- **Edge case for C1:** a stop file at raw stage `build` with `seen` = `test` still reads as stopped in both functions. If the spec wants `seen` to override that, C1 could be reopened, but `intent.md` says a stop counts at `build`.
