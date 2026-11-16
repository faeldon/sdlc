---
id: 069
slug: intent-proposes-serves
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 069 — Intent shows what a change serves in its draft, rather than asking first · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `skills/intent/SKILL.md` Step 1's **What it serves** no longer asks: with a product doc,
   the skill reads it and *proposes* the `serves:` line itself, from the open ids in
   `docs.product.outcomes` or `none`, drawing on the seed or brief, the person's account and the
   doc. It asks no `AskUserQuestion` about outcomes or what they move.
2. R2. It always proposes. When nothing said or seeded points at an outcome, it still proposes one
   (`none` included), marked **inferred** rather than drawn from a named source.
3. R3. For each outcome proposed, it drafts its `- **Moves O<n>:** …` line in Outcome from the
   same sources. With `serves: none` there is no Moves line.
4. R4. Step 3 shows the `serves:` line with a comment naming each outcome and where the proposal
   came from: `serves: [O3]  # proposed from 2026-11-17-1: O3 (Few stops)`, or `# inferred: …`
   under R2. The line written in Step 5 is still `serves: [O3]` alone. The Moves lines are shown
   and written as body text.
5. R5. Step 4's WAIT question names the proposed outcomes, each with its `name`, after the
   change's name: `Create this as <tier> change NNN-<slug> (NNN if still free when created),
   serving O3 (Few stops), …`, or `serving no outcome` for `none`, in its plain, `ids_from:
   github` and Tier 1 plan-mode forms alike. Its answers are unchanged (`yes / change the tier /
   edit a section`, and Tier 1's four); `edit a section` is how the person changes the proposal.
   Without a product doc the question has no `serving` clause.
6. R6. "Never pick for the human" is replaced by the rule that the skill proposes, the person
   decides at the gate, and nothing is written before the yes, with the reason: the retrospective
   counts these, so the question names them.
7. R7. `tests/test_skills.py::test_intent_never_picks_what_a_change_serves` is renamed and
   rewritten to pin R1, R2, R4 and R5: Step 1 says the skill proposes and not the old wording,
   names `inferred`, `none` and `**Moves O1:**`; Step 3 shows the `# proposed from` comment; the
   WAIT section's question names `serving`. It fails if any of these is removed.
8. R8. `docs/REFERENCE.md`'s product-doc paragraph says `/sdlc:intent` proposes the outcomes
   (open ids only) and their Moves lines in its draft and names them in its question, rather than
   "offers".
9. R9. `./check.sh` passes, the existing WAIT tests included (`test_every_wait_asks_in_a_dialog`,
   the 2–4 options check, `test_spec_and_a_tier_one_intent_start_plan_mode_after_their_wait`).

## Design

The whole change is prose in one skill, its pinning test and one reference paragraph. No script,
config key, frontmatter meaning or template changes.

- **Step 1** keeps the read of the product doc (proposing needs it). Its two "ask" sentences become
  one instruction to propose, naming the sources in order (a brief or seed first, then what the
  person said, then the doc's outcomes against the Problem) and the `inferred` fallback. The
  `docs.product`-absent case is untouched.
- **Step 3** already shows `serves:` with a name comment and drops the comment at Step 5; the
  comment's wording grows a source: `proposed from <seed id | your account>` or `inferred`. The
  existing sentence "the line written in Step 5 is `serves: [O1]` alone" stays.
- **Step 4**'s literal question gains a `serving <ids with names>` clause, written once in the
  base template, with a sentence saying the github and Tier 1 forms keep it in the same place. It
  sits before the github clause, since what the change serves is part of what the yes creates.
- **Step 5** is unchanged: it already writes the `serves:` line as approved.
- `/sdlc:spec` is unchanged: its paragraph already shows a changed `serves:` line with the spec,
  never a separate question.

Measuring needs nothing: `metrics.py` counts each `AskUserQuestion` at intent as a `question`
stop on `Sdlc-Stage: intent`, so the retrospective sees `question=` fall once this lands.

## Contracts touched

- **"A skill's WAIT step: what it approves, or when" (always Tier 2).** The yes now approves
  outcomes the skill proposed, where today the person chose them before the gate. It stays inside
  the promise: nothing is written before the yes, the question names the outcomes so the yes
  plainly covers them (R5), and `edit a section` changes them.
- **One WAIT, in a dialog, 2–4 answers.** One heading, the same answers; only the question's text
  grows.
- **Narrow `allowed-tools`.** No new commands.
- **Nothing public names the agent.** Not touched.

## Alternatives rejected

- **Ask when there's no clue.** It keeps a stop exactly where a guess is likeliest to be wrong,
  but the gate names the outcomes, and a marked `inferred` proposal is as checkable as a question
  for one fewer stop. Rejected at the person's call.
- **A separate confirmation dialog for the proposal.** That is today's stop with a pre-filled
  answer: it saves nothing.
- **Have `sdlc.py` propose the outcomes.** Matching a seed's prose to outcomes is judgment, the
  skill's half of mechanism vs. judgment; the script would have nothing deterministic to go on.
- **Show the proposal only in the draft, not the gate.** Easy to approve unread, and the
  retrospective counts the line as the person's decision, so the yes has to cover it visibly.

## Verification

- `uv run --group dev pytest tests/test_skills.py -q`: the rewritten test and the WAIT tests pass.
- `./check.sh`: green.
- At ship, `sdlc.py cases` scopes the `intent` tag, so `run-cases` covers the intent eval with the
  reworded skill. Its fixture has no product doc: the no-product path still ends at its own
  question, with no `serving` clause.
- After it lands, the next closes' `Sdlc-Stage: intent` trailers show `question=0` where the seed
  or account settled what the change serves.
