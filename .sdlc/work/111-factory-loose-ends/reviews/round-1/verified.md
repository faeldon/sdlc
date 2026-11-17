- KEPT: code: C1: plugins/factory/scripts/factory.py:4232: `_up()` returns lost (`True`) for any exit before answering, so a crashing `serve` is started three times and gets false `retries` entries. The intent asks for a retry only when the serve "fails to bind", and nothing checks whether the port is actually taken.

## Notes
- I read `factory.py` (`_up`, `_serve`, `shots`), `intent.md`, `plan.md` and the diff stat. I ran no tests.
- `plan.md` line 18 lists "the server exits before answering" as a retry case, so the builder followed the plan literally. The plan's wording is looser than the intent's "fails to bind". The bind probe fits both: an `EADDRINUSE` exit still fails to bind and is retried, while a crash for another reason now fails at once.
- The existing test `test_shots_take_a_new_port_when_theirs_is_lost` has a port that is "bound but not listening". It should still count as lost after the change, because the probe's bind would fail there too. Re-run it after the fix.
