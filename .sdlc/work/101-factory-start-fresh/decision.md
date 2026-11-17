DECISION: ESCALATE

**Why.** The change is well built and clean after one round. The code reviewer's round 1 is `VERDICT: PASS` with only Optional notes, it found code and a test for every requirement from R1 to R12, the gate passed (`./check.sh` exit 0, 2013 tests) and there is no `decisions.md`. I'm escalating because the change touches things a person should see before anything lands. It changes the policy in AGENTS.md: a new fourth write before a WAIT, which moves a change's branch (fast-forward or rebase) before anyone says yes. It also changes a published interface: a new `factory.py fresh` command, new JSON keys from `start` and `gate`, and a new `gate_jobs` key in `.sdlc/factory.toml`. And its default runs gates one at a time where today they are unlimited. intent.md records that you chose both of these at the run's question, but there's no ledger entry here for me to check that against, so confirm it yourself.

**Open items**
- None required. Optional, from the code reviewer: the edited AGENTS.md lines in *Writes before a WAIT* and *The factory* run past the wrap width, and the four-exception sentence is one long run. Rewrap it.
- Optional, from the code reviewer: `test_a_killed_gate_frees_its_slot` imports `time` inside the function.
- Optional, from the code reviewer: `gate_slot` makes one extra `git rev-parse` call per gate. It's harmless.
- The reviewer didn't read the README wording. R12 leaves that to ship's context-doc pass.
- notes.md: the hand gate (`sdlc.py gate`) takes no slot. That follows the spec; a seed can come later.
- notes.md: `/sdlc-factory:spec` gets `base` and `behind` from `start` but doesn't show them or run `fresh`.

**Decisions to confirm**
- None in a ledger, because there's no `decisions.md`. intent.md says you made two calls:
  - the `fresh` update runs before the WAIT, as a fourth named exception
  - `gate_jobs` defaults to 1, a change from today's unlimited gates that intent.md says is "to be said at ship"

  Confirm that the build matches both.

**For the person at ship**
1. **`cmd_fresh()` in `plugins/factory/scripts/factory.py`.** Check that it only hands off to `sdlc.py base`, `resolve` and `resolve --abort`, with no git step of its own. Check the `held` branch at `stage: build`. Check that the refusal on a failed abort still carries `resolve`'s `undo`.
2. **AGENTS.md *Writes before a WAIT* (line 107 on) and *The factory* (around line 222).** These are the policy edits, and they need the rewrap.
3. **`gate_slot()` and its use in `cmd_gate()`.** Check that the clock starts once the slot is taken, that the platform imports sit inside the functions, and that the descriptor is closed in `finally`.
4. **The default of 1.** Hosts running factory builds side by side will now see their gates queue. The README should say so.
5. **`.sdlc/work/inbox.md`.** The builder said it was already modified in this worktree before the build started. It isn't in the build's file list. Keep it out of this change's commit, since a register entry must never ride on a change's branch.

- IMPACT: minor — hosts gain `factory.py fresh`, an automatic update before a build, and the `gate_jobs` key. Nothing they already have stops working, though by default their factory gates now run one at a time.
