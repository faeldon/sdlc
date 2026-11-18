
**Questions I resolved:**
- **Who resolves a conflict between changes?** One landing agent: the `builder` agent with a new `train-resolve` task, given every change's spec and diff. The Outcome names one landing agent, and the builder is the only role allowed to edit.
- **Re-gate halves, or eject by the files the failing tests touch?** Re-gate prefixes: at most ⌈log₂ n⌉ extra gates per ejection. Ejecting by files would mean reading the host's test runner, which the plugin can't do.
- **Where does an ejected change go?** Back to its commit from before the train (`reset --keep`, undo printed). If it stayed stacked, its branch would hold the commits of the changes before it, and a hand `/sdlc:close` would land them with no `Close`.
- **One board track per train, or one per change?** One per change, with `TRAIN: k of n`. The board reads each change's folder, and there is no folder for a whole train.
- **Selective tests?** Considered and not built, for the same reason as ejecting by files.

**Questions left for you:**
- **Are you OK with the gate weakening?** Only the tip is gated, so the in-between states the base branch passes through are never gated on their own.
- **Should close hold the lock during the tracker call?** From merge to `Close` covers `archive`, so a new change or a filed idea waits for one tracker call per close. The alternative is reordering close, but its `Close` message names where the change was archived.
- **Should a failure in one change eject it, or stop the whole train?** By failure I mean a kept landing change, failing acceptance checks, or a mend used up. My default is eject (R8), so the rest land. Stopping the train is stricter and matches today, where a stop also stops every later change.
- **Where should behaviour checks run?** My default runs each change's check on its own stacked commit, which costs one agent run per moved change. Running every change's check at the tip would also catch a later change breaking an earlier one's path. It would need all n agents in the last change's worktree.
