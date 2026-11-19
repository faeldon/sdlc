# Decisions

- [x] D1 (builder round 1, default): (no decision in the ledger to supersede) Read any `FIX: <answer>` line and go on only for `ALREADY MADE`, instead of the spec's regex that matches only `ALREADY MADE`. Going ahead with that unless told otherwise. → settled by the approver: spec R6 requires refusing a report whose `FIX:` lines disagree, which the design's regex (it matches only `ALREADY MADE`) can never detect. `plan.md` records the departure and why. The code checks the answer against `FIX_MADE`. The extended `test_a_fix_commit_needs_an_ask` covers the disagreeing case. The test, code and security reviews in round 1 each endorse it. The line is internal to the builder's report, which only `factory.py` reads, so it is not a published interface.
  - OPTION: any `FIX:` answer, only `ALREADY MADE` goes on — R6's "lines that disagree" refusal can happen; differs from the design text
  - OPTION: the spec's regex as written — matches the design word for word; two `FIX:` lines can never disagree, so R6's refusal can't happen
  - WHY: R6 asks for disagreeing answers to be refused, and only the wider regex can see a disagreement.
