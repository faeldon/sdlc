# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Where the build differs from the spec and plan

- **Only the newest builder report owes evidence**, `build/round-<built>.md`, so a run started
  before this change keeps its old reports and is checked from its next one. Every
  `behaviour.md` is checked, since none existed before.
- **The check is `RUNS_THE_CHANGE`, a tuple of one,** naming the reviewers whose replies owe
  evidence, so a later role that runs the change joins it by name.
- **A failing command is evidence too:** `exit: 1` satisfies the rule; the rule is that a result
  is shown, not that it is green.

## Found while building

- [x] `plugins/factory/agents/reviewer-test.md` tells the test reviewer to run each `checks.md`
  section's `sh` block itself, which the behaviour check here is told never to do, since an agent
  may have written them and `accept` runs them under a prompt. Pre-existing, outside this spec.
  → seed: 2026-11-04-4
