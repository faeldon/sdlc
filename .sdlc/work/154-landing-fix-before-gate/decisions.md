# Decisions

- [x] D1 (builder round 1, default): For a change that conflicts when stacked, the fix comes after the conflict is resolved, not before the stack. Going ahead with that unless told otherwise. → settled by the approver: the fix comes after a conflict's resolution. The intent's Approach puts the fix "right after `stack`", and its Constraints keep the re-stack unchanged. `plan.md` (step 2: "or its conflict resolved") and `_train_reading()` take the resolution first, so the fix is gated on the commit that will actually land. Both reviewers confirm this order.
  - OPTION: after the resolution — the builder fixes the change as it really sits in the stack, and the train needs no new step; the person's words are applied to code that was just resolved
  - OPTION: before the stack — the fix is on the original change; the stack then re-runs and could conflict again on what the fix touched
  - WHY: the reading already takes the resolution first, and the fix should be gated on the commit that will actually land
- [x] D2 (builder round 1, default): The fix always comes before the gate; there is no way for the person to ask for it after the gate. Going ahead unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: always before the gate — one rule, and the fix is always gated and reviewed in the same round
  - OPTION: let the person choose before or after — covers a fix aimed only at what the landing review would raise; adds a second answer to the yes and a second place the fix can fall
  - WHY: a fix after the gate is exactly the case that got skipped (147's landing); a fix aimed at the review is still reviewed when it comes first
