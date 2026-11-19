# 182 — Plan

> How the Tier 1 Approach is built: it touches four files, so the order and the tests are written
> down here.

## Files to change

- `plugins/factory/agents/approver.md`: the ESCALATE rule's "published interface" clause, and the
  `- ESCALATED: look:` item under *What you return*. A published interface the approved spec's
  *Contracts touched* (at Tier 1, the intent's Contracts or Approach) names, or the person's
  answer in `decisions.md` already settles, goes under *For the person at ship*, with no line and
  no ESCALATE on that ground alone. A Critical or High finding still open, a disagreement, a
  departure, a requirement with no test, a destructive operation and a secret stay looks. Each
  look's reason starts with its target: `- ESCALATED: look: <what to look at> — <why>`.
- `plugins/factory/skills/decide/SKILL.md`: Step 1's look item names the target (the reason's
  text before ` — `, else the whole reason) in the question, and says `seen` records it as
  acknowledged and accepted as built, `checked something` what the person verified.
- `plugins/factory/README.md`: the decide bullet says the same in a clause.
- `tests/test_skills.py`: two tests pinning the wordings.

No change to `factory.py`, `factory_records.py` or `REASON_RE`: the target is part of the
reason's free text, which `REASON_RE` already takes whole. `prompts/approve.md` words no
escalation rule, so it is left alone.

## Work order

1. Slice 1, the approver's rule: a test on `approver.md` (red), then the wording.
2. Slice 2, decide's look item: a test on decide's `SKILL.md` (red), then the wording and the
   README clause.

## Tests

- `test_the_approver_raises_a_look_only_for_what_no_one_approved`: the covered-by-the-spec rule,
  that it lands under *For the person at ship*, the kinds that stay looks whatever the spec says,
  and the `<what to look at> — <why>` form.
- `test_decide_names_what_a_look_asks_to_see`: the question names the target, and says what
  `seen` and `checked something` record.
- The existing `test_decide_asks_each_look_and_runs_nothing_for_a_gate` and
  `test_the_approver_gives_every_reason_a_line_with_its_kind` still pass, so the answers and the
  `- ESCALATED: <kind>:` form are unchanged.

## Rollback

Prose and tests only: `git revert` undoes it all.
