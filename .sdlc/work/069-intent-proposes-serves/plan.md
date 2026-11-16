---
id: 069
slug: intent-proposes-serves
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 069 — Intent shows what a change serves in its draft, rather than asking first · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Files to change

- `skills/intent/SKILL.md`: Step 1's **What it serves** proposes the `serves:` and
  `**Moves O<n>:**` lines instead of asking (R1–R3, R6); Step 3's comment names the proposal's
  source (R4); Step 4's question gains a `serving <O1 (Unaided setup)>` clause, `serving no
  outcome` for `none`, kept in the github and Tier 1 forms, left out without a product doc (R5).
- `tests/test_skills.py`: `test_intent_never_picks_what_a_change_serves` becomes
  `test_intent_proposes_what_a_change_serves_and_its_gate_names_it` (R7).
- `docs/REFERENCE.md`: the product-doc paragraph says intent proposes and names them (R8).

## Work order

1. Rewrite Step 1's paragraph, Step 3's `serves:` example and Step 4's question in the skill.
2. Rewrite the pinning test; run `pytest tests/test_skills.py`.
3. Edit the reference paragraph; run `./check.sh`.

## Tests

- R1–R4, R6, R7: `test_intent_proposes_what_a_change_serves_and_its_gate_names_it` (Step 1
  proposes, names `inferred`, `none`, `**Moves O1:**`, and not the old wording; Step 3 shows
  `# proposed from` and `# inferred`).
- R5: the same test asserts the WAIT names `serving <O1 (Unaided setup)>` and
  `serving no outcome`; `test_every_gate_offers_two_to_four_answers` (via `GATE_QUESTION_RE`)
  and `test_spec_and_a_tier_one_intent_start_plan_mode_after_their_wait` still pass, so the
  answers and the Tier 1 form are unchanged.
- R8: manual: read `docs/REFERENCE.md`'s product-doc paragraph.
- R9: `./check.sh`.
- Manual, at ship: `sdlc.py cases` scopes `intent`; `run-cases` (paid, the person's call) shows
  the no-product path still ends at its own question.

## Rollback

`git revert <sha>` restores the skill's questions, the test and the reference paragraph. Nothing
outside the repo is created; intents written while this was live keep their approved `serves:`
lines, which mean the same either way.
