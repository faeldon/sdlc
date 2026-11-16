---
id: 069
slug: intent-proposes-serves
tier: 2
impact: minor
stage: shipped
created: 2026-11-17
updated: 2026-11-17
shipped: 2026-11-17
idea: 2026-11-17-1
depends_on:
serves: [O3]
---

# 069 — Intent shows what a change serves in its draft, rather than asking first

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

Every one of the 27 changes closed since 2026-11-04 asked at least one question at intent beyond
its gate, 33 in all. Most were the product-doc questions in Step 1 of `skills/intent/SKILL.md`:
which outcomes the change serves, and what each should move. The skill makes them questions by
rule ("Never pick for the human"), even when the seed already says what the work is for. As a
result, the median Tier 2 change stops 8 times against O3's target of 6, and the median Tier 1
change 6 against 5. Raised by the retrospective of 2026-11-17. This intent is a case in point: it
asked both questions, and its seed had already answered them.

## Outcome

- With a product doc, `/sdlc:intent` drafts the `serves:` line and each `**Moves O<n>:**` line
  from the seed (or the person's account) and the product doc, and shows them in Step 3's draft,
  marked as proposed, with no question of their own. The WAIT's `edit a section` answer is how the
  person changes them, so the yes stays their decision, made at the gate.
- When nothing said or seeded points at an outcome, the draft still proposes one (`none`
  included) and says it was inferred, so the person checks it.
- `tests/test_skills.py::test_intent_never_picks_what_a_change_serves` is rewritten to pin the
  new rule: proposed in the draft, approved at the WAIT, never written before the yes.
- **Moves O3:** intent asks nothing beyond its gate when the seed and product doc settle what it
  serves, so the median Tier 2 change's stops fall from 8 toward 6 and Tier 1's from 6 toward 5.

## Affected

- **Area:** the intent skill's interview and draft (Steps 1 and 3).
- **Files & components:** `skills/intent/SKILL.md`; `tests/test_skills.py` (the test above);
  `docs/REFERENCE.md`'s product-doc paragraph ("`/sdlc:intent` offers only the open outcomes…");
  possibly `skills/spec/SKILL.md`, whose matching paragraph shows a changed `serves:` line with
  the spec.
- **Downstream:** every host with a `docs.product`, whose intents start carrying a proposed line
  where they carried a chosen one. `/sdlc:retro`'s product pass reads `serves:` and `moves` as the
  person's decision, so it relies on the gate really reviewing them. `sdlc.py check` still
  requires the line, unchanged.
- **Contracts:** "A skill's WAIT step: what it approves, or when" (always Tier 2): the yes now
  approves an outcome choice the skill proposed. No script, config key or frontmatter meaning
  changes.

## Constraints

- Nothing is written before the yes: the proposal lives only in the draft.
- The proposal uses only the open ids in `docs.product.outcomes`, or `none`, each shown with its
  `name`.
- The retrospective's counts must stay the person's judgment: a proposal waved through unread is
  a guess counted as a decision, so the draft has to make the proposed lines easy to spot.
- `sdlc-factory`'s spec skill writes no `serves:` today, and stays out of scope.

## Open questions

- ~~How is "proposed" marked in the draft: a comment on the `serves:` line, a note beside the
  Outcome lines, or both, and what keeps the mark out of the written file?~~ Resolved: the
  `serves:` line's existing comment names the source (`# proposed from <seed id>: O3 (Few
  stops)`, or `# inferred: …`), Step 5 already drops it, and the WAIT question names the outcomes
  (spec R4, R5).
- ~~When the seed gives no clue, propose anyway or fall back to asking? Asking keeps today's stop
  exactly where a guess is likeliest to be wrong.~~ Resolved: always propose, marked `inferred`;
  the gate question names it (spec R2).
- ~~Does `/sdlc:spec` change to match (propose, not show a changed line), or is its paragraph
  already right?~~ Resolved: already right; it shows a changed line with the spec and asks
  nothing separately.
- ~~Is the 33-question figure counted from `Sdlc-*` trailers, so the retro can show the drop, or
  does a stop need a new record?~~ Resolved: `metrics.py` counts each intent `AskUserQuestion` as
  `question=` on `Sdlc-Stage: intent`; no new record.
