VERDICT: PASS

All three round-4 asks are already in the working tree, and the factory tests pass (209 in `tests/test_factory.py`, with the port subset at 51). I found no Critical or Required finding.

- **TIME_WAIT (kept finding, `_binds()`):** the probe sets `SO_REUSEADDR` on non-Windows, and `test_a_server_that_answered_and_closed_first_has_not_lost_its_port` runs a real connection that the server closes first, then exits with its port free, and asserts `lost` is False. I reproduced the mechanism outside the repo: after a server-closes-first, a bind fails without the option and succeeds with it. A listening holder and a bound-only holder both still read as held with it.
- **Exit without answering (`_up()`'s non-answered branch):** it now returns `_lost(host, port)`, so a port that binds is not lost. `test_a_server_that_fails_on_its_own_is_started_once` runs `exit 1` and asserts one start, no `retries`, and `problem` set.
- **Answered, then exited (`_up()`'s answered branch):** it returns `_lost(host, port)` too. `test_a_port_is_lost_only_when_it_wont_bind_whichever_way_the_server_ended` drives `_up()` with a stub whose `poll()` returns 1 after its listener closes, and asserts `lost` is False when the port frees and True when it stays held.

I did not mutate the code to watch the new tests fail. The TIME_WAIT check above shows the mechanism they depend on.

## Notes

- Windows skips `SO_REUSEADDR` by design. I could not check that path here, so it rests on the docstring's reasoning.
- If a `[ui] serve` shell exits while a child it spawned still holds the port, `_binds()` reads the port as held and the start is retried as lost. That matches the rule as written ("only a port that won't bind is lost"), but the retry log then blames another process when it was the server's own child. This is a note, not a change.
- Lint (`ruff check`, `ruff format --check`) is clean on both reworked files.
