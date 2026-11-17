# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build departs from the spec

- **R5's `--to` is gone.** `factory.py agent` files each reply itself, by the build's own rules
  (`build/round-<R+1>.md`, `reviews/round-N/<role>.md`, `verified.md`, `decision.md`, a mend over
  the reply it mends), instead of taking a path from the skill. It takes `--task` (`spec`, `build`,
  `review`, `verify`, `rework`, `decided`, `mend`, `approve`), `--role` and `--decision`, and
  builds every prompt from `verdicts`' state (`loop_state()`), so no free text a person typed
  passes through a bash argument. It refuses a task `verdicts` didn't name.
- **R2's "only writes"** leaves out that the supervisor still ticks `decisions.md` with the
  person's answers, as the build session always did.
- **R12's role mapping** uses `runs/<agent>.sessions` outright: no transcript names a `--agent`
  role (`agentName` is a session title; headless sessions are `entrypoint: sdk-cli`).
- **The `claude` call has no pin of its own**: `tests/test_windows.py`'s scan of every script's
  `subprocess.run` already holds it to text mode in UTF-8 and no shell.
- **Found on the way:** `metrics.read_events` rebound its `ident` parameter for a tool result's
  id, so a typed `/sdlc:close` on `main` was missed in every session read after the first tool
  result. Fixed, with `test_a_close_on_main_is_found_in_a_session_read_after_a_tool_result`.

## Not verified yet

- [x] A real supervised run (paid): from the main checkout, `/sdlc-factory:build` on a scratch
  Tier 2 at `plan`, then a second before the first's draft lands. It is the only check that
  shows `claude -p --agent sdlc-factory:<role>` loads the plugin's agent in a headless session,
  honours the builder's `Agent(Explore, Plan)` allowlist (the docs say so for `claude --agent`,
  and say nothing of `-p` or a plugin-qualified name), runs in `factory.mode`, and that the
  transcripts land where `measure` reads them. → seed: 2026-11-17-7
