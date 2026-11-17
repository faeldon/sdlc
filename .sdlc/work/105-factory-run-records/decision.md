DECISION: READY

**Why.** Code review round 1 passed with no Critical or Required findings. The reviewer found code and a named test for every requirement R1–R11, and the factory's gate passed `./check.sh` on this build (2034 tests, ruff, plugin validation). There is no `decisions.md` and no `notes.md`, so nothing is assumed without you and no item was carried over. The places the build departs from the spec are all recorded in plan.md's *As built* section, and none of them changes what a requirement asks for.

**Open items**
- None. The code reviewer's optional suggestion: the spec skill could say outright that a failed `agent --task spec` shows nothing, so an old `runs/spec-draft.md` is never shown as new. Its Step 1 already reads the draft only after a successful run.

**Decisions to confirm**
- None. No ledger exists and the builder raised none. The intent's one open question is struck, and its answers (the 3-hour window, keeping the draft files after `write-spec`, the spec skill moving to `factory.py agent`) were yours at the run's question.

**For the person at ship**
- **`.sdlc/work/inbox.md` is changed in the worktree** (three seeds marked `[building]`). It is not in the build's file list (`round-1.files`), but it would be swept in if the commit takes everything. AGENTS.md says a register entry never rides on a change's branch, so leave it out of this commit and send it through `inbox-commit` on the base branch.
- **`scripts/sdlc.py`: `factory_first_build()` and the `cmd_check` branch that asks it.** This weakens `check --strict`, which is a gate. Confirm three things:
  - it hides only the template-plan problem;
  - all four conditions plus the 3-hour mtime bound are checked;
  - an unreadable `step.md` counts as not live.
  
  `test_a_live_first_build_hides_no_other_problem` and the six-case negative test are the ones that pin this.
- **`factory.py`: `split_draft()`'s fence tracker (`FENCE_MARK_RE`) and `cmd_decisions()`'s rewrite of a superseded line.** The rewrite must touch only the target line, and a rerun must change nothing.
- **`agent --task spec`'s JSON no longer has `reply`.** Both factory skills were updated in step with it. Anything outside the plugin that read `reply` would break.
- The reviewer didn't run the by-hand scratch-repo checks from spec §Verification, so the byte-for-byte draft and the stale-session cases are proven only by the tests.

- IMPACT: minor — factory users get a new `write-spec` command, a `(supersedes D<n>)` form for defaults, and spec drafts that come through whole even with fenced code. `check --strict` stops flagging a live first build's plan. Nothing anyone already relies on needs to change, apart from `agent --task spec`'s JSON dropping `reply`, which only the plugin's own skills read.
