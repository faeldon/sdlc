I've read all three claims against the code and the ship skill's conflict steps, and I'm about to return my answers.

- **C1:** the `reload_error` text sends people to restart. `current()` reloads whenever the mtime changes, so a fixed file recovers without a restart.
- **C2:** the comment on line 603 claims "at any stage", but the code only handles a missing stage and a closed one. `column()` puts any card with problems under needs-you.
- **C3:** a card with `rebasing` set falls through to the stage's normal next step. `sdlc.py resolve <NNN>` is the command the ship skill already names.

- KEPT: code: C1: scripts/board.py:720: reload_error tells people to restart, but `current()` reloads on the next change to the file — the message sends them to do unneeded work
- KEPT: ux: C2: scripts/board.py:603: the comment says a problem is the next step at any stage, but `next_action` only handles a missing stage and a closed one, so a needs-you card at intent, spec, build or test still reads "/sdlc:spec" or "/sdlc:ship" under its red problem line
- KEPT: ux: C3: scripts/board.py:619: a `rebasing` card falls through to "build it, then /sdlc:ship" or "/sdlc:ship" while its rebase is stopped, and nothing in `next_action` reads `rebasing`

## Notes
I ran no tests and no commands that write. I read `next_action`, `column`, `_Live.current` and `_load` in `scripts/board.py`. I also read where `rebasing` is computed (line 99) and shown (`board.html`), and grepped `skills/ship/conflict.md` for `sdlc.py resolve <NNN>`. I didn't open `test_the_running_board_serves_board_py_as_it_is_on_disk`; the C1 claim rests on `current()`'s mtime check.

The fix for C3 should say "resolve" or "abort and redo", using `sdlc.py resolve <NNN>` and `resolve <NNN> --continue` from `skills/ship/conflict.md`. The abort command is the one I didn't confirm, so the builder should check it in that file.
