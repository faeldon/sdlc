
**Resolved**

- *What counts as "vanished" for a seed?* The code answers it. A seed leaves the register through a `Close` commit (its change's `idea:` or `fixes:`), which makes it done. It can also leave through `inbox-commit`'s `Retire <id>` with a reason, which makes it dropped. Gone with neither record, as by a hand edit, is vanished. A seed still in the register is carried, whether or not an open change claims it (R7).
- *Where do `fixes:` lines come from for closed changes?* From the intent, read by `_change_record()` (R4). The `Sdlc-Fixes:` trailer is missing on `Close` commits from before it existed.
- *The three metrics.py nits:* each is fixed with a test (R11–R13), not just answered.

**Left for the person**

- **How a change with mixed signals is classed.** The draft uses this precedence: fix, then capability, then process, then debt. A declared fix is the person's stated reason for the change, and impact describes the release. The overlap stays visible in `also` and `mixed`. Putting capability first would class a fix that needed a new option as capability: the mix would show more capability work and fewer fixes, and it would stop agreeing with change failure rate, which reads the same `fixes:`/`reworks:` lines. Either way the change is one reordered tuple and one test expectation.
- **Proposed intents can't be counted.** Nothing records the intent titles a retrospective proposes, so `follow_through.missing` names them. Counting them needs the retro skill to record them somewhere history keeps, for example as seeds marked `Priority: high`. That's a change to a skill with a WAIT, so it belongs in its own change. Should it be filed as a seed?
- **Should `direction.milestones` say `retired`?** It reports a retired grouped seed as `vanished`. That's a different meaning from follow-through's `vanished`, in the same JSON. This draft leaves it alone because it's outside the intent. Aligning it would be a small follow-up.
