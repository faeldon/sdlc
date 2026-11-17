VERDICT: PASS

## Notes

**Requirements, walked against the code:**
- **Outcome 1 (ui and ux of one round run together):** `shots()` now writes under `.sdlc/reports/shots/<change>/<label>/<role>/`, so each role gets its own `fixture/`, `serve.log` and `shots.json`. `_fixture_copy()` and `_serve()` already work inside whatever `where` they are given, so nothing else is shared. `cmd_agent()` passes `role` for both `review` and `land-review` labels.
- **Outcome 2 (a test that fails while they share a folder):** `test_the_ui_and_ux_reviews_of_a_round_run_at_once` runs two `cmd_agent` threads behind a barrier, using a serve stub that refuses an existing `drafts/`. On the old layout the second serve hits the first's `drafts/` and returns exit 1, so the test fails. The barrier sits after the fixture copy, so the copies overlap as they would in a real run.
- **Outcome 3 (no supervisor step between them):** `build/SKILL.md` already says to start every reviewer in `missing` "in one message" (line 336). Nothing in the skill or README works around the old collision, so no skill change is needed.
- **Constraints:** the host's `[ui] serve` is unchanged, and `{fixture}` now points at a per-role path. Reviewer prompts receive their screenshot paths from `cmd_agent()`, so the prompts need no edit. The `.gitignore` under `reports/` still ignores everything.

**Checks I ran:**
- `uv run --group dev pytest -q tests/test_factory.py`: 211 passed.
- `ruff check plugins tests` and `ruff format --check plugins tests`: clean.
- `git grep` for `shots --round` and `factory.py shots` in tracked files: no caller outside the tests and prose. The `--role` flag is therefore not a contract break for any skill or doc.

**Notes:**
- The `shots` CLI subcommand now requires `--role`. Nothing in the repo invokes it, but any external script that calls `factory.py shots --round N` will need `--role`. Low risk for an internal subcommand.
- Existing `round-<n>/shots.json` files from earlier runs are no longer reused, since the path changed. Each run re-shoots once. Harmless.
- I did not re-run the new test repeatedly to check for timing flakiness. The barrier's 20 s timeout and the `_fixture_copy` call happening once per try look safe, unless a port is lost, which would call the wrapper again and could break the barrier. I'd like the author to confirm the new test passes a few times in a row under `-n auto`.
- `timeout` isn't on this machine's PATH, so I ran pytest without it.

**What's done well:** the fix is the smallest change that gives each role its own resources, and it leaves the host's serve contract alone. The test reproduces the reported collision (a server that refuses a shared `drafts/`), not just the path string.
