
**Open questions I answered**

- **With no goal stated, does the run take the direction doc's top goal unasked?** No. `--preview` proposes one (R4): the first open milestone with a candidate, else the busiest theme. The question names it, so the person's yes approves it. `--begin` takes only the goal the preview named (R6). Picking another is a new preview. This follows from the intent's Outcome ("the yes approves the goal along with the caps").
- **Who finds a goal "suggested from the register": the script or the planner?** The script, from the candidates' themes and counts (R4). `--preview` writes nothing and may not start a paid session before the WAIT (`preview()`'s contract, `test_autopilot_preview_writes_nothing`).
- **What does the planner's reply become?** The `- WAVE:` list grows a tier and a reason, inside groups named by the risk they lower, with `- WAITS:` and `- LEAVE:` lines. Every candidate is placed once. It's filed as the reply is today, parsed into `state["plans"]`, and shown in the summary (R8, R11). There is no separate plan file.
- **How does "checks each against the code" fit inside Read/Grep/Glob, and what happens to a seed called wrong?** The planner reads. The script checks that a `fixed`/`wrong` LEAVE cites a path that exists. That seed is left: never opened, offered again, retired or filed, and it's listed under "Left for you" (R8, R9, the intent's Constraints).
- **Is "the backlog grew faster than it drained" measured over the run or against the last retrospective's register size?** Over the run: ids filed against ids gone, from the register at `--begin` and at the end (R11). The retrospective's size isn't held anywhere autopilot reads, and it covers a different window.

**Left for you**

- **Should `--begin` refuse a goal with no candidate within the bounds?** The draft only warns, and such a run ends at its first wave. Refusing saves a run that does nothing, but costs one more refusal to learn.
- **Should an `off-goal` LEAVE be listed under "Left for you" too?** The draft lists it only in "The plan", because it isn't a defect in the seed. Listing it would make the summary longer, but every seed the run passed over would be in one place.
