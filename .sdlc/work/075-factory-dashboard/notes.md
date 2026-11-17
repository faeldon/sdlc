# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build differs from the spec

- **R10: `/sdlc:dashboard` doesn't run `sdlc.py config`.** The board reads no config key the skill
  needs, and `/sdlc:status`, the other read-only skill, runs none either; a call that reads nothing
  would only add a permission rule. The skill's one command is `board`.
- **R2: a request naming another host is a 404.** Not in the spec: a page elsewhere that points its
  own name at 127.0.0.1 (DNS rebinding) could otherwise read the change folders through the board.
  The Host header must be `127.0.0.1:<port>` or `localhost:<port>`.
- **R14: the shots go under `.sdlc/reports/shots/<change>/<label>/`**, `round-<N>` for a build's
  round and `land-<n>` for a landing's review, since `land-review` reaches the UI reviewers too.
- **The board's first screenshots caught two bugs** (R19's check, run by hand through `shots()`
  with this worktree's `[ui]`, since `main` has none yet): six columns overflowed at 1280px
  (minimum width now 168px), and the phone shot fired before `/state.json` answered, showing an
  empty board. The second is the screenshot command's to wait for, so this repo's `shoot` passes
  Playwright's `--wait-for-selector '.col'`, and the factory README says a page that fills in
  after loading needs one. The retaken shots show every column at 1280px and stacked at 390px.
- **`{out}` is relative to the checkout.** The first run's `shots.json` held absolute paths under
  the home folder, which `test_nothing_local.py` reads (it scans ignored files too) and would fail
  on in this repo after any UI review; the command runs from the checkout, so the relative path
  works, and a test pins it.
- **Rebased onto 073, 076 and 077 before ship**, as `wip 075`. Four files conflicted, each
  resolved by keeping both sides: 073's gate and this change's UI clause in build's Step 1 and both
  WAIT questions; `max_runs()` counting the gate's fixes and the UI reviewers (26 by default, 32
  with `[ui]`); both subcommands; the README's agents table and run count; AGENTS.md's factory
  paragraph, where `shots` is no longer called the one place the factory runs a host's commands,
  since 073's gate is another. 073 had added its own `_sh()` copy and pin, so this change's
  duplicates were dropped.
- **074 landed during this build**, so the board's cost reads `runs/costs.jsonl` as it shipped,
  with the run's time summed beside `run_cost()`'s figures (pinned key by key).
