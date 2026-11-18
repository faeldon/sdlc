# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## While building

- The spec's "how a hand-built change comes to have shots is left open" stays open. `factory.py
  shots <NNN> --round <n> --role ui|ux` already works from a hand-built change's own worktree
  (`find_change()` only needs the branch and its `intent.md`). Neither `passes.ui.why` nor
  `ui.md` names it, so ship never points at a command that starts a dev server.
- Some existing tests pinned shapes this spec extends, so they changed with it:
  - every exact `Sdlc-Findings` string gains ` passes=0 passes_wrong=0` (R10);
  - the `By must be one of` message and the `FINDING_BY` pin gain `SHIP_PASSES` (R9);
  - the no-file record gains `passes` and `evidence`;
  - the deep-diff ship test now needs `Security review:` as well (R2, R11);
  - `test_sdlc_loads_nothing_from_plugins` now lists the three core agents beside `reviewer.md`;
  - `test_carry_writes_each_agent_finding_once_by_its_role`'s trailer tail changed.
- The `FULL` example question in `SKILL.md` shows no pass clause. It is the one sentence pinned
  byte for byte, and adding to it would cost the line budget.
- [x] Say in `ui.md`, or in `passes.ui.why` when `sdlc-factory` is enabled, how a hand-built → seed: 2026-11-18-57
  change takes its screenshots (`factory.py shots`), once the person decides whether ship should
  point at a command that starts a dev server.
