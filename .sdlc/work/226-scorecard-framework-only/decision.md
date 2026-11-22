DECISION: ESCALATE

**Why:** The build looks complete. Round 2 is `VERDICT: PASS` from both reviewers, the gate is green, and no S-ids or wave headings remain in the scorecard. D2, D3 and D4 are open defaults about policy and scope, which I may not settle or confirm. D4 also departs from the intent's word-for-word constraint. So the person has to decide them first.

**Open items**
- None. Round 2 left no unresolved CHANGE.

**Decisions to confirm**
- ESCALATED: D2: This is a release-policy question, which only the person can decide. The intent lists it as an open question and never answers it. The build assumed no release rule beyond *Release due*.
- ESCALATED: D3: This is about scope, whether metrics marked *not captured* get seeds in the register. The intent lists it as an open question. The build filed none, and only the person can choose to fill the register.
- ESCALATED: D4: The build removed seed ids from outside the Status lines. That goes past the intent's word-for-word constraint and the outcome's list, so the person must accept the scope change. It supersedes D1, which kept the ids.

**For the person at ship**
- Look first at `docs/RETRO-SCORECARD.md`. Check that it ends after *Hosts*, that the four prose spots lost their seed ids (the lead-time paragraph, the Feedback-loop and Landing time bullets, and the Hosts opening), and that the questions table is unchanged.
- Then check that `.sdlc/SDLC.md` has lost its wave-based release block, and that `docs/CONTRIBUTING.md` no longer says "and the seeds that build it".
- Both reviewers read `checks.md` and did not run it. The behaviour reviewer did not count the 36 Status lines or check the last `##` heading. `tests/test_retro.py` and `test_defaults.py` were covered only by the gate, which passed.
- No published interface is touched.

- IMPACT: none — only contributor docs and this repo's own process doc change; nothing a host or release holder receives.

**Undone items**
- UNDONE: Five lines in `docs/RETRO-SCORECARD.md` already ran past 100 columns (35, 44, 176, 452, 454); untouched here. → dropped: the lines were already long before this change. The notes give no rule that requires wrapping them, and the edit would touch the framework text that must stay word for word.
