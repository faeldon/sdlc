# Decisions

- [x] D1 (builder round 1, default): A `decided` run's row uses `state["round"]`, falling back to `state["built"]`, because `loop_state` names no round while it waits on a decision. Going ahead with that. → settled by the approver: R2 says `decided` is `build` in the run's first round and `rework` after it, which needs a round to compare. `cmd_agent` takes `state["round"] or state["built"]` (`factory.py:4398`) because `loop_state` names no round while it waits on a decision. `test_purpose_by_task_and_round` pins the round mapping, and the code and test reviewers raised nothing against it. This is an internal tagging detail, not scope or policy.
  - OPTION: round or built — puts the answer in the round it builds on, so a later round's answer counts as rework; the cost is that it relies on a fallback
  - OPTION: no round on the row — simplest; but a `decided` run would always be tagged `build`, and the rework it does after round 1 wouldn't count as waste
  - WHY: R2 says `decided` is `build` in the run's first round and `rework` after it, which needs a round to compare.
- [x] D2 (builder round 1, default): The waste line's untagged count is the number of runs (`2 runs untagged`); the changes those runs belong to are already named in its missing-reasons. Going ahead with that. → settled by the approver: R9 asks the waste coverage line to "name the untagged count", and R7's `untagged` block is counted in `runs`. The changes those runs belong to are already counted in the line's missing reasons (`runs recorded before purposes N`). The behaviour round's real report shows `172 runs untagged`, and `test_the_report_says_how_far_cost_and_waste_rest` pins it. This is the wording of a report line, not a published interface.
  - OPTION: runs — says how much spend sits outside every share
  - OPTION: changes — duplicates the missing-reason count already on the line
  - WHY: R9 asks the line to name the untagged count, and the change count is already there.
