VERDICT: PASS

## Notes

**Trust boundaries the diff touches.** Close is in `[review] sensitive`. Three of its boundaries matter here:
- **The host's `close_cleanup` command.** It comes from config, runs through `_sh()`, and is read from the base branch as it stood before the merge.
- **The push to the remote.** This is the one place close publishes.
- **The handoff to the merged script.** In this repo only, close runs code that came from the branch.

The diff adds one data path: the text of an exception raised while timing the lead goes into close's JSON report (`measure.errors`).

**STRIDE:**
- **Tampering.** Can a change's branch loosen its own close?
  - `close_cleanup` still comes from `_config_at(main, start)`, the base's config before the merge. `_close_preview` is the old code moved word for word.
  - The handoff guard `_merged_scripts()` still requires `PLUGIN_DIR == main` and `HANDOFF_ENV != "merged"`.
  - The new code passes `c.own_repo`, which is always a bool. The old code had rebound `own` to the list of unpushed commits. So in a host repo, the handoff check can no longer be reached through a truthy list. It was blocked before as well by the `PLUGIN_DIR` comparison, but the guard is now stricter.
- **Repudiation and Denial of service.** The lock span hasn't moved:
  - The `ExitStack` loop in `_run_close_steps` is a word-for-word copy.
  - The lock is taken at step 0 and let go after `remove folder`, or after `record` for a drop.
  - `tell_issues` runs after the lock is let go.
  - A close run from inside the worktree still exits 3.
- **Information disclosure.** `measure.errors` goes only to the report on stdout, which nothing commits. The message is cut to 200 characters, and no trailer changes. Run files and transcripts on the local machine are its only source. Low risk, and nothing to fix.
- **Elevation of privilege.** None of the git flags changed. Old and new both use `merge --ff-only`, `worktree remove` without `--force`, `branch -d`, and `update-ref -d` only on the change's own `BASE_REF` and resolve refs. `_push()` is untouched and never forced.

**Checks I made:**
- **Line by line against the old code.** I compared `cmd_close` at HEAD (`/tmp` copy, lines 708–1076) with the new `_close_target`, `_close_refusals`, `_close_preview`, `_close_steps`, `_run_close_steps` and the `_step_*` functions. The refusals, their order, and the early return on `trunk_refusal` are the same, and the report keys are written in the same order.
  - One difference: a refusal that the archive is set up wrong, together with a named change, now reaches `_close_refusals` through `c.branch`. It still adds to the same refusals list and still exits 1 before anything is written.
- **The push invariant.** The rewrite of `test_only_the_named_steps_push` (D3) makes it stricter, not weaker:
  - It matches `_push(` as a whole word, so `_step_push` no longer slips through as a substring.
  - It requires `_push`'s callers to be exactly `{cmd_publish, _step_push, cmd_release}`.
  - It requires `_run_close_steps` to be the only caller of `_step_push`.
  - It still requires `_push_plan(` where close sets up its push, now `_close_preview`.

  `_run_close_steps` calls `_step_push` only when `c.plan["on"]`, the result of `_push_plan`.
- **No new subprocess, text write or platform-only module.** The `math` import in `sdlc.py` is stdlib. The R9 ceiling change only affects arithmetic. It rounds down, so it can't raise spending above the cap.
- **The new fixture `tests/fixtures/close-output.json`.** I searched it for home paths, `/private/`, tokens and secrets and found none. Temp paths are normalised to `<tmp>`.
- **The gate.** `build/round-1.gate.md` is `GATE: PASS` (`./check.sh`, exit 0, build `6b5313a3aa45823c`). I didn't run it again.

**Decisions D1–D4.** None of them has a security effect. D1's plain class is safe: it behaves like the dataclass, with nothing evaluated when the file loads.

**What is done well:**
- The lock is still taken and let go in one function, so one read shows the whole span it guards.
- No step table is built when the file loads, so a test's stand-in still reaches every step.
- The characterization test pins the push-to-bare-remote scenario, the one that publishes.

- NIT: scripts/closing.py:396: `measure.errors` holds the raw exception text. In the plugin's own repo, a child after a handoff passes it up unchanged. It's local stdout only, but if a future reader of the run files puts a path or a line of content in a message, that text lands in close's report, so say in the docstring that the message is meant for the person running close and must never become a trailer {docs S low}
