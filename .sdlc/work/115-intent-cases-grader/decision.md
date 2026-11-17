DECISION: READY

**Why.** The only review round passed with no Critical or Required findings, the gate is green (2197 passed, 9 skipped), and there's no `decisions.md` and no `notes.md`, so no unconfirmed assumption and nothing left undone. The plan answers the intent's open question: `claude plugin eval` reads `focus: trace` from a grader's frontmatter, and the code reviewer confirmed that key in the 2.1.311 binary. So the Approach's first branch held and `skills/intent/SKILL.md` is untouched, as the constraints ask. Outcome 2 (two runs agree) can't be shown by the diff. The intent puts those paid runs behind ship's prompt, so that's where it gets settled.

**Open items.** None are CHANGE findings. The code reviewer's notes still matter at ship:
- The draft and question always surviving trace truncation is claimed but not checked. Past 24 messages only the first and last 12 are kept, so a tier or draft given earlier in a long run could be cut. (code)
- Outcomes 1 and 2 aren't proven until the paid runs happen. (code)
- `intent.md` lists "the cases' suite file" under Affected, but `plan.md` doesn't touch one or say why. Probably right, since there's no such file in `evals/`. (code)
- The test pins the wording "before its final question" as well as `focus: trace`, so harmless rewording of the criteria would break it. (code)

**Decisions to confirm.** None. No decisions were raised.

**For the person at ship.**
1. **Run the paid cases first.** Run `intent` and `intent-product` twice each, as the Approach asks. In one run's `--json` trace, count the messages:
   - If a run goes past about 24 messages and the tier or draft lands in the cut middle, the trace focus doesn't fully deliver Outcome 1. The fallback is the Approach's second branch: the prompt asks for the draft and question in one message.
   - If the two runs disagree, the change hasn't met Outcome 2 and shouldn't land.
2. **Read the two grader texts.** These are `evals/intent/graders/judgment.md` and `evals/intent-product/graders/judgment.md`. The "judge only the agent's own `text` blocks" instruction is what stops the judge passing on SKILL.md's own example headings, which the trace now contains.
3. **Check `test_a_judgment_grader_reads_the_whole_reply` in `tests/test_evals.py`.** Decide whether the wording assertion should stay.

- IMPACT: none — only this repo's paid eval graders, one test and a CONTRIBUTING sentence changed; nothing a host or plugin user receives behaves differently.

There are no undone items: the change has no `notes.md`. There are no recovery lines: the prompt names no irreversible paths, and `plan.md`'s rollback is `git revert`.
