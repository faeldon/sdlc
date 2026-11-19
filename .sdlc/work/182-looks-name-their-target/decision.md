I've read all of the change's files. I'm settling D2 and escalating D1, then writing up the decision.

DECISION: ESCALATE

**Why.** Both round-2 reviews passed and the round-2 gate is green (`./check.sh`, 3158 passed). Round 1's one kept change (the outdated look line in `docs/REFERENCE.md`) and its nit are both fixed, and the build follows `plan.md` with `factory.py` and `REASON_RE` left as they were. The only reason to escalate is D1. It decides when a published interface no longer stops for the person. The intent left that as an open question, and only the person can answer it.

**Open items**
- None. Round 2 is all `VERDICT: PASS` (code, behaviour), and F1 and F2 in `findings.md` are both `fixed`.

**Decisions to confirm**
- ESCALATED: D1: This decides when an approver can skip a look on a published interface, which is escalation policy about a published interface, so it isn't mine to settle. The intent's *Open questions* left it open ("the reason appearing in the spec's *Contracts touched*, or the person's own words in `decisions.md`?"). The builder took "either" from the Constraints line, and `approver.md:47-51` is built on that answer.
- SETTLED: D2: The intent answers it. Its Constraints say "No change to how `factory.py` parses decisions or ledgers", and its *Affected* Contracts say the `- ESCALATED: <kind>: <why>` line "stays as `REASON_RE` reads it". That rules out a parsed field. Its Approach says "each look's reason starts with what to look at", which is the target-first prose form that was built (`approver.md:100-103`, `docs/REFERENCE.md:543-545`). Both round-2 reviews confirmed that `REASON_RE` still reads it whole.

**For the person at ship**
- Read `plugins/factory/agents/approver.md:38-55` first. The new paragraph "What the person already approved is no look" is the rule D1 asks you to confirm: the spec's or intent's contracts, **or** a `→ decided:` answer, count as approval. A settled or assumed default never does.
- Then read `plugins/factory/skills/decide/SKILL.md:77-83`. Check that the look question quotes the text before ` — ` and says what `seen` and `checked something` record, and that the WAIT and its answers are unchanged.
- The new tests (`test_the_approver_raises_a_look_only_for_what_no_one_approved`, `test_decide_names_what_a_look_asks_to_see` in `tests/test_skills.py`) only check that the wording is present. They don't show that an approver follows it, as round 1's code review noted.
- This change rewrites the approver's own prompt. This decision was made under the prompt as it stood before the change.

- IMPACT: patch — factory runs raise fewer needless looks, and each look names its target. The `ESCALATED` line still parses as before, and decide's answers are unchanged, so no one holding the previous release has to do anything differently.
