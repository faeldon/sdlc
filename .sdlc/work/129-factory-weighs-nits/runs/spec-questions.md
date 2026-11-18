Spec-writer: a few things you should know before approving.

**Behaviour changes to check:**
- **Batches with nits no longer land on their own.** Any factory change with a nit to file now needs your approval at landing, because nothing may be filed without your yes. The alternative is to file nothing under an auto landing, which would quietly lose those nits.
- **Ship-by-hand now files agent nits too.** I put this in scope (R12) because a factory change shipped by hand would otherwise still lose its nits. It edits `skills/ship/factory.md`, and you can cut it.
- **Over the cap, 5 nits are filed and the rest recorded unfiled** (R6), plus a signal. The alternative is to refuse the landing until you look.

**Open questions I answered from the code:**
- **Who weighs them?** The reviewer that raised each one, in its own `- NIT:` line. The script then turns the weights into a disposition. The approver has no shell and runs after the last round, so a cheap nit could never reach the builder in the same run.
- **Does a `fix` nit go to the builder in the same run, or at landing?** Same run, only inside a rework that is happening anyway. Fixing at landing would mean a whole new review round and a lasting signal. If no rework runs, the nit is filed in the inbox instead. `sdlc.py ship` refuses any `fix` left in `findings.md`, so one is never left there.
- **Is a nit a later round stops raising dropped?** No. Only a `fix` nit that was handed to the builder and not raised again counts as `fixed`. Every other nit is filed, because a reviewer's silence on it says nothing about whether the code changed.

**For you to decide:**
1. Nits to file block auto-landing (my default), or nits aren't filed when a batch lands on its own.
2. Keep or cut R12, ship filing a hand-shipped factory change's agent nits.
3. Over 5 nits: file the first 5 and raise a signal (my default), or keep the change out of the batch until you've seen it.
